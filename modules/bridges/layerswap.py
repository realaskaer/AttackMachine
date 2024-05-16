import json

from modules import Bridge, Logger
from modules.interfaces import BridgeExceptionWithoutRetry
from settings import WAIT_FOR_RECEIPT_BRIDGE


class LayerSwap(Bridge, Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)
        Bridge.__init__(self, client)

    async def get_networks_data(self):
        url = "https://api.layerswap.io/api/v2/networks"

        return (await self.make_request(url=url, headers=self.headers))['data']

    async def get_swap_limits(self, source_chain, destination_chain, source_asset, destination_asset, _):
        url = "https://api.layerswap.io/api/v2/limits"

        params = {
            "source_network": source_chain,
            "source_token": source_asset,
            "destination_network": destination_chain,
            "destination_token": destination_asset,
        }

        response = (await self.make_request(url=url, headers=self.headers, params=params))['data']

        min_amount = response['min_amount']
        max_amount = response['max_amount']

        return min_amount, max_amount

    async def get_swap_fee(self, source_chain, destination_chain, source_asset, destination_asset, amount):
        url = "https://api.layerswap.io/api/v2/quote"

        params = {
            "source_network": source_chain,
            "destination_network": destination_chain,
            "source_token": source_asset,
            "destination_token": destination_asset,
            "amount": amount,
        }

        response = (await self.make_request(url=url, headers=self.headers, params=params))['data']['quote']

        fee_amount = response['total_fee']
        receive_amount = response['min_receive_amount']

        return fee_amount, receive_amount

    async def get_swap_data(
            self, amount, source_chain, destination_chain, source_asset, destination_asset, refuel
    ):

        url = "https://api.layerswap.io/api/v2/swaps"

        create_swap_data = {
            "source_network": source_chain,
            "destination_network": destination_chain,
            "source_token": source_asset,
            "destination_token": destination_asset,
            "amount": amount,
            "source_address": self.client.address,
            "destination_address": self.client.address,

        }

        return await self.make_request(
            method='POST', url=url, headers=self.headers, json=create_swap_data
        )

    async def create_tx(self, swap_data):

        swap_id = swap_data['data']['swap']['id']

        url = f"https://api.layerswap.io/api/v2/swaps/{swap_id}"

        params = {
            'from_address': f"{self.client.address}"
        }

        response = await self.make_request(url=url, headers=self.headers, params=params, json=swap_data)

        call_data = response['data']['deposit_actions'][0]['call_data']
        to_address = response['data']['deposit_actions'][0]['to_address']

        return call_data, to_address

    async def bridge(self, chain_from_id: int, bridge_data: tuple, need_check: bool = False):
        (source_chain, destination_chain, amount, to_chain_id, from_token_name,
         to_token_name, from_token_address, to_token_address) = bridge_data
        source_asset, destination_asset, refuel = from_token_name, to_token_name, False

        bridge_info = f'{self.client.network.name} -> {destination_asset} {destination_chain}'
        if not need_check:
            self.logger_msg(*self.client.acc_info, msg=f'Bridge on LayerSwap: {amount} {source_asset} {bridge_info}')

        networks_data = await self.get_networks_data()

        available_for_swap = {
            chain['name']: [(asset['symbol'], asset['decimals']) for asset in chain['tokens']
                            if asset['symbol'] in [from_token_name, to_token_name]][0]
            for chain in networks_data if chain['name'] in [source_chain, destination_chain]
        }

        if (len(available_for_swap) == 2 and available_for_swap[source_chain]
                and available_for_swap[destination_chain]):

            data = source_chain, destination_chain, source_asset, destination_asset, amount

            min_amount, max_amount = await self.get_swap_limits(*data)
            fee_amount, receive_amount = await self.get_swap_fee(*data)

            if need_check:
                return round(float(fee_amount), 6)

            if float(min_amount) <= amount <= float(max_amount):

                amount_in_wei = self.client.to_wei(amount, available_for_swap[source_chain][1])

                swap_data = await self.get_swap_data(amount, *data)
                call_data, to_address = await self.create_tx(swap_data)

                if from_token_name != self.client.token:
                    value = 0
                else:
                    value = amount_in_wei

                transaction = (await self.client.prepare_transaction(value=value)) | {
                    'to': self.client.w3.to_checksum_address(to_address),
                    'data': call_data
                }

                old_balance_on_dst = await self.client.wait_for_receiving(
                    token_address=to_token_address, token_name=to_token_name, chain_id=to_chain_id,
                    check_balance_on_dst=True
                )

                await self.client.send_transaction(transaction)

                self.logger_msg(*self.client.acc_info,
                                msg=f"Bridge complete. Note: wait a little for receiving funds", type_msg='success')

                if WAIT_FOR_RECEIPT_BRIDGE:
                    return await self.client.wait_for_receiving(
                        token_address=to_token_address, token_name=to_token_name,
                        old_balance=old_balance_on_dst, chain_id=to_chain_id
                    )
                return True

            else:
                raise BridgeExceptionWithoutRetry(f"Limit range for bridge: {min_amount} - {max_amount} ETH")
        else:
            raise BridgeExceptionWithoutRetry(f"Bridge {source_asset} {bridge_info} is not active!")
