from utils.tools import gas_checker, repeater
from config import TOKENS_PER_CHAIN, HELP_SOFTWARE
from settings import SLIPPAGE, UNLIMITED_APPROVE
from modules import Aggregator, Logger


class Rango(Aggregator, Logger):
    def __init__(self, client):
        Logger.__init__(self)
        super().__init__(client)

    async def get_quote(self, from_token_address, to_token_address, from_token_name, to_token_name, amount):
        api_key = 'ffde5b24-ee86-4f47-a1c8-b22d8f639a38'
        url = f'https://api.rango.exchange/routing/best?apiKey={api_key}'

        headers = {
            'content-type': 'application/json;charset=UTF-8',
            "accept": "*/*"
        }

        quote_payload = {
            'from':
                {
                    'blockchain': 'ZKSYNC',
                    'symbol': from_token_name,
                    'address': from_token_address
                },
            'to':
                {
                    'blockchain': 'ZKSYNC',
                    'symbol': to_token_name,
                    'address': to_token_address
                },
            "selectedWallets": {"ZKSYNC": self.client.address},
            "connectedWallets": [{
                "blockchain": "ZKSYNC",
                "addresses": [self.client.address]
            }],
            'amount': amount,
            'checkPrerequisites': True,
            'slippage': SLIPPAGE
        } | ({'affiliateRef': "gd0C76", "affiliatePercent": 1,
             "affiliateWallets": {"ZKSYNC": "0x000000a679C2FB345dDEfbaE3c42beE92c0Fb7A5"}} if HELP_SOFTWARE else {})

        return await self.make_request(method='POST', url=url, headers=headers, json=quote_payload)

    async def get_swap_data(self, request_id):

        api_key = 'ffde5b24-ee86-4f47-a1c8-b22d8f639a38'
        url = f'https://api.rango.exchange/tx/create?apiKey={api_key}'

        headers = {
            'content-type': 'application/json;charset=UTF-8',
            "accept": "*/*"
        }

        swap_payload = {
            "userSettings": {
                "slippage": SLIPPAGE,
                "infiniteApprove": UNLIMITED_APPROVE
            },
            "validations": {
                "balance": True,
                "fee": True,
                "approve": True
            },
            "requestId": request_id,
            "step": 1
        }

        return await self.make_request(method='POST', url=url, headers=headers, json=swap_payload)

    @repeater
    @gas_checker
    async def swap(self):

        from_token_name, to_token_name, amount, amount_in_wei = await self.client.get_auto_amount(class_name='Rango')

        self.logger_msg(
            *self.client.acc_info, msg=f"Swap on Rango.Exchange: {amount} {from_token_name} -> {to_token_name}")

        token_data = TOKENS_PER_CHAIN[self.client.network.name]

        from_token_address = None if from_token_name == "ETH" else token_data[from_token_name]
        to_token_address = None if to_token_name == "ETH" else token_data[to_token_name]

        data = from_token_address, to_token_address, from_token_name, to_token_name, amount

        quote_data = await self.get_quote(*data)

        swap_data = await self.get_swap_data(quote_data['requestId'])

        tx_params = (await self.client.prepare_transaction(value=amount_in_wei if from_token_name == "ETH" else 0)) | {
            'data': swap_data['transaction']['data'],
            'to': self.client.w3.to_checksum_address(swap_data['transaction']['to'])
        }

        return await self.client.send_transaction(tx_params)
