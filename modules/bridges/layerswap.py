import json

from config import TOKENS_PER_CHAIN
from modules import Bridge, Logger
from general_settings import GLOBAL_NETWORK
from utils.tools import gas_checker, helper


class LayerSwap(Bridge, Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)
        Bridge.__init__(self, client)

    async def get_networks_data(self):
        url = "https://api.layerswap.io/api/available_networks"

        headers = {
            'Content-Type': 'application/json'
        }

        return (await self.make_request(url=url, headers=headers))['data']

    async def get_swap_rate(self, source_chain, destination_chain, source_asset, destination_asset, refuel):
        url = "https://api.layerswap.io/api/swap_rate"

        swap_rate_data = {
            "source": source_chain,
            "destination": destination_chain,
            "source_asset": source_asset,
            "destination_asset": destination_asset,
            "refuel": refuel
        }

        return (await self.make_request(method='POST', url=url, headers=self.headers,
                                        data=json.dumps(swap_rate_data)))['data']

    async def get_swap_id(self, amount, dst_address, source_chain, destination_chain,
                          source_asset, destination_asset, refuel):
        url = "https://api.layerswap.io/api/swaps"

        create_swap_data = {
            "source": source_chain,
            "destination": destination_chain,
            "source_asset": source_asset,
            "destination_asset": destination_asset,
            "amount": amount,
            "destination_address": f'{dst_address}',
            "refuel": refuel
        }

        return (await self.make_request(method='POST', url=url, headers=self.headers,
                                        data=json.dumps(create_swap_data)))['data']

    async def create_tx(self, swap_id):
        url = f"https://api.layerswap.io/api/swaps/{swap_id}/prepare_src_transaction"

        params = {
            'from_address': f"{self.address_to_hex(self.client.address)}"
        }

        return (await self.make_request(url=url, headers=self.headers, params=params))['data']

    @staticmethod
    def address_to_hex(address:str | int):
        if isinstance(address, int):
            return hex(address)
        elif isinstance(address, str):
            return hex(int(address, 16))

    @helper
    @gas_checker
    async def bridge(self, chain_from_id: int, private_keys:dict = None):
        if GLOBAL_NETWORK == 9 and chain_from_id == 9:
            await self.client.initialize_account()
        elif GLOBAL_NETWORK == 9 and chain_from_id != 9:
            await self.client.session.close()
            self.client = await self.client.initialize_evm_client(private_keys['evm_key'], chain_from_id)

        (source_chain, destination_chain,
         amount, to_chain_id) = await self.client.get_bridge_data(chain_from_id, 'LayerSwap')

        source_asset, destination_asset, refuel = 'ETH', 'ETH', False

        bridge_info = f'{self.client.network.name} -> {destination_asset} {destination_chain.capitalize()[:-8]}'
        self.logger_msg(*self.client.acc_info, msg=f'Bridge on LayerSwap: {amount} {source_asset} {bridge_info}')

        networks_data = await self.get_networks_data()

        available_for_swap = {
            chain['name']: (assets['asset'], assets['decimals'])
            for chain in networks_data if chain['name'] in [source_chain, destination_chain]
            for assets in chain['currencies'] if assets['asset'] in [source_asset, destination_asset]
        }

        if (len(available_for_swap) == 2 and source_asset in available_for_swap[source_chain]
                and destination_asset in available_for_swap[destination_chain]):

            data = source_chain, destination_chain, source_asset, destination_asset, refuel

            min_amount, max_amount, fee_amount = (await self.get_swap_rate(*data)).values()

            if float(min_amount) <= amount <= float(max_amount):

                _, balance, _ = await self.client.get_token_balance(source_asset)

                if balance >= amount:
                    amount_in_wei = int(amount * 10 ** available_for_swap[source_chain][1])
                    dst_address = await self.get_address_for_bridge(private_keys['evm_key'], stark_key_type=False)

                    if source_chain == 'STARKNET_MAINNET' and destination_chain != 'STARKNET_MAINNET':
                        swap_id = await self.get_swap_id(amount, dst_address, *data)

                        tx_data = await self.create_tx(swap_id['swap_id'])

                        transfer_call = self.client.prepare_call(
                            contract_address=TOKENS_PER_CHAIN['Starknet']['ETH'],
                            selector_name="transfer",
                            calldata=[
                                int(self.address_to_hex(tx_data['to_address']), 16),
                                amount_in_wei, 0
                            ]
                        )

                        watch_data = json.loads(tx_data['data'])[1]
                        watch_call = self.client.prepare_call(
                            contract_address=int(self.address_to_hex(watch_data['contractAddress']), 16),
                            selector_name="watch",
                            calldata=watch_data['calldata']
                        )

                        transaction = transfer_call, watch_call
                    else:

                        if source_chain != 'STARKNET_MAINNET' and destination_chain == 'STARKNET_MAINNET':
                            dst_address = await self.get_address_for_bridge(private_keys['stark_key'],
                                                                            stark_key_type=True)

                        swap_id = await self.get_swap_id(amount, dst_address, *data)

                        tx_data = await self.create_tx(swap_id['swap_id'])

                        transaction = [(await self.client.prepare_transaction(value=amount_in_wei)) | {
                            'to': self.client.w3.to_checksum_address(tx_data['to_address']),
                            'data': tx_data['data']
                        }]

                    old_balance_on_dst = await self.client.wait_for_receiving(to_chain_id, check_balance_on_dst=True)

                    result = await self.client.send_transaction(*transaction)

                    self.logger_msg(*self.client.acc_info,
                                    msg=f"Bridge complete. Note: wait a little for receiving funds", type_msg='success')

                    await self.client.wait_for_receiving(to_chain_id, old_balance_on_dst)

                    return result

                else:
                    raise RuntimeError("Insufficient balance!")
            else:
                raise RuntimeError(f"Limit range for bridge: {min_amount} - {max_amount} ETH")
        else:
            raise RuntimeError(f"Bridge {source_asset} {bridge_info} is not active!")
