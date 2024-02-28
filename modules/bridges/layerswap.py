import json

from modules import Bridge, Logger
from modules.interfaces import BridgeExceptionWithoutRetry
from utils.tools import helper


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

    async def get_swap_id(self, amount, source_chain, destination_chain,
                          source_asset, destination_asset, refuel):
        url = "https://api.layerswap.io/api/swaps"

        create_swap_data = {
            "source": source_chain,
            "destination": destination_chain,
            "source_asset": source_asset,
            "destination_asset": destination_asset,
            "amount": amount,
            "destination_address": self.client.address,
            "refuel": refuel
        }

        return (await self.make_request(method='POST', url=url, headers=self.headers,
                                        data=json.dumps(create_swap_data)))['data']

    async def create_tx(self, swap_id):
        url = f"https://api.layerswap.io/api/swaps/{swap_id}/prepare_src_transaction"

        params = {
            'from_address': f"{self.client.address}"
        }

        return (await self.make_request(url=url, headers=self.headers, params=params))['data']

    @helper
    async def bridge(self, chain_from_id: int, bridge_data: tuple, need_check: bool = False):
        (source_chain, destination_chain, amount, to_chain_id, from_token_name,
         to_token_name, from_token_address, to_token_address) = bridge_data
        source_asset, destination_asset, refuel = from_token_name, to_token_name, False

        bridge_info = f'{self.client.network.name} -> {destination_asset} {destination_chain}'
        if not need_check:
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

            min_amount, max_amount, fee_amount, receive_amount = (await self.get_swap_rate(*data)).values()

            if need_check:
                return round(float(fee_amount), 6)

            if float(min_amount) <= amount <= float(max_amount):

                amount_in_wei = self.client.to_wei(amount, available_for_swap[source_chain][1])

                swap_id = await self.get_swap_id(amount, *data)
                tx_data = await self.create_tx(swap_id['swap_id'])

                if from_token_name != self.client.token:
                    value = 0
                else:
                    value = amount_in_wei

                transaction = (await self.client.prepare_transaction(value=value)) | {
                    'to': self.client.w3.to_checksum_address(tx_data['to_address']),
                    'data': tx_data['data']
                }

                old_balance_on_dst = await self.client.wait_for_receiving(
                    token_address=to_token_address, token_name=to_token_name, chain_id=to_chain_id,
                    check_balance_on_dst=True
                )

                await self.client.send_transaction(transaction)

                self.logger_msg(*self.client.acc_info,
                                msg=f"Bridge complete. Note: wait a little for receiving funds", type_msg='success')

                return await self.client.wait_for_receiving(
                    token_address=to_token_address, token_name=to_token_name,
                    old_balance=old_balance_on_dst, chain_id=to_chain_id
                )

            else:
                raise BridgeExceptionWithoutRetry(f"Limit range for bridge: {min_amount} - {max_amount} ETH")
        else:
            raise BridgeExceptionWithoutRetry(f"Bridge {source_asset} {bridge_info} is not active!")
