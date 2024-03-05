import web3
from eth_account.messages import encode_structured_data
from modules import DEX, Logger, Client, RequestClient
from modules.interfaces import SoftwareException
from utils.tools import gas_checker, helper
from config import (
    BEBOP_CONTRACTS,
    TOKENS_PER_CHAIN
)


class Bebop(DEX, Logger, RequestClient):
    def __init__(self, client: Client):
        self.client = client
        Logger.__init__(self)
        self.network = self.client.network.name
        self.router_address = BEBOP_CONTRACTS[self.network]['router']

    async def get_data_to_sign(self, from_token_address: str, to_token_address: str, amount_in_wei: int):
        url = f'https://api.bebop.xyz/{self.client.network.name.lower()}/v2/quote'

        params = {
            'buy_tokens': to_token_address,
            'sell_tokens': from_token_address,
            'sell_amounts': amount_in_wei,
            'taker_address': self.client.address
        }

        response = await self.make_request(url=url, params=params)
        if response.get('error'):
            raise SoftwareException(response['error']['message'])

        min_amount_in_wei = int(response['buyTokens'][to_token_address]['amount'])
        data_to_sign = response['toSign']
        quote_id = response['quoteId']

        return min_amount_in_wei, data_to_sign, quote_id

    async def get_order_data(self, from_token_address, to_token_address, amount_in_wei):

        min_amount_out, data_to_sign, quote_id = await self.get_data_to_sign(
            from_token_address, to_token_address, amount_in_wei
        )

        data_to_sign['taker_amounts'] = [[int(*i)] for i in data_to_sign['taker_amounts']]
        data_to_sign['maker_amounts'] = [[int(*i)] for i in data_to_sign['maker_amounts']]
        data_to_sign['commands'] = self.client.w3.to_bytes(hexstr=data_to_sign['commands'])

        typed_data = {
            "domain": {
                "name": "BebopSettlement",
                "version": "1",
                "chainId": self.client.chain_id,
                "verifyingContract": f"{self.router_address}"
            },
            "primaryType": "Aggregate",
            "types": {
                "EIP712Domain": [
                    {
                        "name": "name",
                        "type": "string"
                    },
                    {
                        "name": "version",
                        "type": "string"
                    },
                    {
                        "name": "chainId",
                        "type": "uint256"
                    },
                    {
                        "name": "verifyingContract",
                        "type": "address"
                    }
                ],
                "Aggregate": [
                    {
                        "name": "expiry",
                        "type": "uint256"
                    },
                    {
                        "name": "taker_address",
                        "type": "address"
                    },
                    {
                        "name": "maker_addresses",
                        "type": "address[]"
                    },
                    {
                        "name": "maker_nonces",
                        "type": "uint256[]"
                    },
                    {
                        "name": "taker_tokens",
                        "type": "address[][]"
                    },
                    {
                        "name": "maker_tokens",
                        "type": "address[][]"
                    },
                    {
                        "name": "taker_amounts",
                        "type": "uint256[][]"
                    },
                    {
                        "name": "maker_amounts",
                        "type": "uint256[][]"
                    },
                    {
                        "name": "receiver",
                        "type": "address"
                    },
                    {
                        "name": "commands",
                        "type": "bytes"
                    }
                ]
            },
            "message": {
                **data_to_sign
            }
        }

        text_encoded = encode_structured_data(typed_data)
        sing_data = self.client.w3.eth.account.sign_message(text_encoded, private_key=self.client.private_key)

        return min_amount_out, self.client.w3.to_hex(sing_data.signature), quote_id

    @helper
    @gas_checker
    async def swap(self):
        from functions import wrap_eth, unwrap_eth

        url = f'https://api.bebop.xyz/{self.client.network.name.lower()}/v2/order'

        from_token_name, to_token_name, amount, amount_in_wei = await self.client.get_auto_amount()

        self.logger_msg(*self.client.acc_info, msg=f'Swap on SpaceFi: {amount} {from_token_name} -> {to_token_name}')

        from_token_address = TOKENS_PER_CHAIN[self.network][from_token_name]
        to_token_address = TOKENS_PER_CHAIN[self.network][to_token_name]

        min_amount_out, order_signature, quote_id = await self.get_order_data(
            from_token_address, to_token_address, amount_in_wei
        )

        await self.client.price_impact_defender(from_token_name, amount, to_token_name, min_amount_out)

        if from_token_name == 'ETH':
            await wrap_eth(self.client.account_name, self.client.private_key, self.client.network,
                           self.client.proxy_init, amount_in_wei)

        if from_token_name != 'ETH':
            await self.client.check_for_approved(from_token_address, self.router_address, amount_in_wei)

        payload = {
            'signature': order_signature,
            'quote_id': quote_id,
        }

        response = (await self.make_request(method="POST", url=url, json=payload))

        if response.get('error'):
            raise SoftwareException(response['error']['message'])
        elif response['status'] == 'Success':
            tx_hash = response['txHash']
        else:
            raise SoftwareException(f'Bad request to Bebop API(Order): {response}')

        if from_token_name != 'ETH':
            await unwrap_eth(self.client.account_name, self.client.private_key, self.client.network,
                             self.client.proxy_init, amount_in_wei)

        return await self.client.send_transaction(tx_hash=tx_hash)
