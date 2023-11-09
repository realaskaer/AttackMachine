import aiohttp

from utils.tools import gas_checker, repeater
from config import ZKSYNC_TOKENS, HELP_SOFTWARE
from settings import SLIPPAGE_PERCENT, UNLIMITED_APPROVE
from modules import Aggregator


class Rango(Aggregator):
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
            "affiliateWallets": {"ZKSYNC": "0x000000a679C2FB345dDEfbaE3c42beE92c0Fb7A5"},
            "connectedWallets": [{
                "blockchain": "ZKSYNC",
                "addresses": [self.client.address]
            }],
            'amount': amount,
            'checkPrerequisites': True,
            'affiliateRef': "gd0C76",
            "affiliatePercent": 1,
            'slippage': SLIPPAGE_PERCENT
        } | {'affiliateRef': "gd0C76", "affiliatePercent": 1} if HELP_SOFTWARE else {}

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
                "slippage": SLIPPAGE_PERCENT,
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

        from_token_name, to_token_name, amount, amount_in_wei = await self.client.get_auto_amount()

        self.client.logger.info(
            f'{self.client.info} Rango | Swap on Rango.Exchange: {amount} {from_token_name} -> {to_token_name}')

        from_token_address = None if from_token_name == "ETH" else ZKSYNC_TOKENS[from_token_name]
        to_token_address = None if to_token_name == "ETH" else ZKSYNC_TOKENS[to_token_name]

        data = from_token_address, to_token_address, from_token_name, to_token_name, amount

        quote_data = await self.get_quote(*data)

        swap_data = await self.get_swap_data(quote_data['requestId'])

        tx_params = (await self.client.prepare_transaction(value=amount_in_wei if from_token_name == "ETH" else 0)) | {
            'data': swap_data['transaction']['data'],
            'to': self.client.w3.to_checksum_address(swap_data['transaction']['to'])
        }

        tx_hash = await self.client.send_transaction(tx_params)

        await self.client.verify_transaction(tx_hash)
