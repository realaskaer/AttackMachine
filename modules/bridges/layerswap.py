import json

from modules import Bridge
from utils.tools import gas_checker, repeater


class LayerSwap(Bridge):
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

    async def get_swap_id(self, amount, source_chain, destination_chain, source_asset, destination_asset, refuel):
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
            'from_address': self.client.address
        }

        return (await self.make_request(url=url, headers=self.headers, params=params))['data']

    @repeater
    @gas_checker
    async def bridge(self, chain_from_id, help_okx:bool = False, help_network_id:int = 1):

        source_chain, destination_chain, amount, refuel = await self.client.get_bridge_data(chain_from_id, help_okx,
                                                                                        help_network_id, 'LayerSwap')

        source_asset, destination_asset = 'ETH', 'ETH'

        bridge_info = f'{self.client.network.name} -> {destination_asset} {destination_chain.capitalize()[:-8]}'
        self.client.logger.info(
            f'{self.client.info} Bridge on LayerSwap: {amount} {source_asset} {bridge_info}')

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

                    swap_id = await self.get_swap_id(amount, *data)

                    tx_data = await self.create_tx(swap_id['swap_id'])

                    amount_in_wei = int(amount * 10 ** available_for_swap[source_chain][1])

                    tx_params = (await self.client.prepare_transaction(value=amount_in_wei)) | {
                        'to': self.client.w3.to_checksum_address(tx_data['to_address']),
                        'data': tx_data['data']
                    }

                    return await self.client.send_transaction(tx_params)

                else:
                    raise RuntimeError("Insufficient balance!")
            else:
                raise RuntimeError(f"Limit range for bridge: {min_amount} - {max_amount} ETH")
        else:
            raise RuntimeError(f"Bridge {source_asset} {bridge_info} is not active!")
