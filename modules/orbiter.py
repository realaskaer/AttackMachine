from modules import Bridge
from utils.tools import repeater, gas_checker


class Orbiter(Bridge):
    async def get_bridge_data(self, from_chain: int, to_chain:int, token_name: str):

        url = 'https://openapi.orbiter.finance/explore/v3/yj6toqvwh1177e1sexfy0u1pxx5j8o47'

        request_data = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "orbiter_getTradingPairs",
            "params": []
        }

        response = await self.make_request(method='POST', url=url, json=request_data)

        data = response['result']['ruleList']
        bridge_data = {}

        path = f'{from_chain}-{to_chain}:{token_name}-{token_name}'

        for chain_data in data:
            if chain_data['pairId'] == path:
                bridge_data = {
                    'maker': chain_data['sender'],
                    'fee': chain_data['tradingFee'],
                    'decimals': chain_data['fromChain']['decimals'],
                    'min_amount': chain_data['fromChain']['minPrice'],
                    'max_amount': chain_data['fromChain']['maxPrice'],
                }
        if bridge_data:
            return bridge_data
        raise RuntimeError(f'That bridge is not active!')

    @repeater
    @gas_checker
    async def bridge(self, chain_from_id:int, help_okx:bool = False, help_network_id:int = 1):

        from_chain, to_chain, token_name, amount = await self.client.get_bridge_data(chain_from_id, help_okx,
                                                                                     help_network_id, 'Orbiter')

        bridge_info = f'{amount} {token_name} from {from_chain["name"]} to {to_chain["name"]}'
        self.client.logger.info(f'{self.client.info} Orbiter | Bridge on Orbiter: {bridge_info}')

        bridge_data = await self.get_bridge_data(from_chain['chainId'], to_chain['chainId'], token_name)
        destination_code = 9000 + to_chain['id']
        fee = int(float(bridge_data['fee']) * 10 ** bridge_data['decimals'])
        min_price, max_price = bridge_data['min_amount'], bridge_data['max_amount']
        amount_in_wei = int(amount * 10 ** bridge_data['decimals'])

        tx_params = (await self.client.prepare_transaction(value=amount_in_wei + destination_code + fee)) | {
            'to': bridge_data['maker']
        }

        if min_price <= amount <= max_price:

            _, balance_in_wei, _ = await self.client.get_token_balance(token_name)
            if balance_in_wei >= tx_params['value']:

                tx_hash = await self.client.send_transaction(tx_params)

                await self.client.verify_transaction(tx_hash)

            else:
                raise RuntimeError(f'Insufficient balance!')
        else:
            raise RuntimeError(f"Limit range for bridge: {min_price} – {max_price} {token_name}!")
