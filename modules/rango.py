import aiohttp
from utils.tools import gas_checker, repeater
from config import ZKSYNC_TOKENS, HELP_SOFTWARE
from settings import SLIPPAGE_PERCENT, UNLIMITED_APPROVE
from modules import Client


class Rango(Client):
    def __init__(self, account_number, private_key, network, proxy=None):
        super().__init__(account_number, private_key, network, proxy)
        self.proxy = self.request_kwargs.get('proxy', '')

    async def get_quote(self, payload: dict):
        api_key = 'ffde5b24-ee86-4f47-a1c8-b22d8f639a38'
        url = f'https://api.rango.exchange/routing/best?apiKey={api_key}'

        headers = {
            'content-type': 'application/json;charset=UTF-8',
            "accept": "*/*"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, proxy=self.proxy) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    self.logger.error(f"{self.info} Bad request to Rango(Quote) API: {response.status}")

    async def get_swap_data(self, payload: dict):

        api_key = 'ffde5b24-ee86-4f47-a1c8-b22d8f639a38'
        url = f'https://api.rango.exchange/tx/create?apiKey={api_key}'

        headers = {
            'content-type': 'application/json;charset=UTF-8',
            "accept": "*/*"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, proxy=self.proxy) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    self.logger.error(f"{self.info} Bad request to Rango(Tx data) API: {response.status}")

    @repeater
    @gas_checker
    async def swap(self):

        from_token_name, to_token_name, amount, amount_in_wei = await self.get_auto_amount()

        self.logger.info(f'{self.info} Swap on Rango.Exchange: {amount} {from_token_name} -> {to_token_name}')

        from_token_address = None if from_token_name == "ETH" else ZKSYNC_TOKENS[from_token_name]
        to_token_address = None if to_token_name == "ETH" else ZKSYNC_TOKENS[to_token_name]

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
            "selectedWallets": {"ZKSYNC": self.address},
            "affiliateWallets": {"ZKSYNC": "0x000000a679C2FB345dDEfbaE3c42beE92c0Fb7A5"},
            "connectedWallets": [{
                "blockchain": "ZKSYNC",
                "addresses": [self.address]
            }],
            'amount': amount,
            'checkPrerequisites': True,
            'affiliateRef': "gd0C76",
            "affiliatePercent": 1,
            'slippage': SLIPPAGE_PERCENT
        } | {'affiliateRef': "gd0C76", "affiliatePercent": 1} if HELP_SOFTWARE else {}

        quote_data = await self.get_quote(payload=quote_payload)

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
            "requestId": quote_data['requestId'],
            "step": 1
        }

        swap_data = await self.get_swap_data(payload=swap_payload)

        tx_params = (await self.prepare_transaction(value=amount_in_wei if from_token_name == "ETH" else 0)) | {
            'data': swap_data['transaction']['data'],
            'to': self.w3.to_checksum_address(swap_data['transaction']['to'])
        }

        tx_hash = await self.send_transaction(tx_params)

        await self.verify_transaction(tx_hash)
