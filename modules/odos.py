import aiohttp
from modules import Client
from utils.tools import gas_checker, repeater
from settings import SLIPPAGE_PERCENT
from config import ZKSYNC_TOKENS, ZERO_ADDRESS, ODOS_CONTRACT, HELP_SOFTWARE


class Odos(Client):
    def __init__(self, account_number, private_key, network, proxy=None):
        super().__init__(account_number, private_key, network, proxy)

    async def get_quote(self, from_token_address: str, to_token_address: str, amount_in_wei: int):
        quote_url = "https://api.odos.xyz/sor/quote/v2"

        quote_request_body = {
            "chainId": 324,
            "inputTokens": [
                {
                    "tokenAddress": f"{from_token_address}",
                    "amount": f"{amount_in_wei}",
                }
            ],
            "outputTokens": [
                {
                    "tokenAddress": f"{to_token_address}",
                    "proportion": 1
                }
            ],
            "slippageLimitPercent": SLIPPAGE_PERCENT,
            "userAddr": f"{self.address}",
            "compact": True,
        } | {"referralCode": 2336322279} if HELP_SOFTWARE else {}

        headers = {
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url=quote_url, headers=headers, json=quote_request_body,
                                    proxy=self.proxy) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    self.logger.error(
                        f"{self.info} Bad request to Odos Quote API: {response.status}")

    async def assemble_transaction(self, path_id):
        assemble_url = "https://api.odos.xyz/sor/assemble"

        assemble_request_body = {
            "userAddr": f"{self.address}",
            "pathId": path_id,
            "simulate": False,
        }

        headers = {
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url=assemble_url, headers=headers, json=assemble_request_body,
                                    proxy=self.proxy) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    self.logger.error(
                        f"{self.info} Bad request to Odos Transaction Assembly API: {response.status}")

    @repeater
    @gas_checker
    async def swap(self, help_deposit:bool = False):

        from_token_name, to_token_name, amount, amount_in_wei = await self.get_auto_amount()

        if help_deposit:
            self.logger.warning(f'{self.info} Not enough to deposit on lending! Starting swap module')

            to_token_name = 'ETH'

        self.logger.info(f'{self.info} Swap on Odos: {amount} {from_token_name} -> {to_token_name}')

        from_token_address = ZERO_ADDRESS if from_token_name == "ETH" else ZKSYNC_TOKENS[from_token_name]
        to_token_address = ZERO_ADDRESS if to_token_name == "ETH" else ZKSYNC_TOKENS[to_token_name]

        if from_token_name != 'ETH':
            await self.check_for_approved(from_token_address, ODOS_CONTRACT["router"], amount_in_wei)

        path_id = (await self.get_quote(from_token_address, to_token_address, amount_in_wei))["pathId"]
        transaction_data = (await self.assemble_transaction(path_id))["transaction"]

        tx_params = (await self.prepare_transaction()) | {
            "to": transaction_data["to"],
            "data": transaction_data["data"],
            "value": int(transaction_data["value"]),
        }

        tx_hash = await self.send_transaction(tx_params)

        await self.verify_transaction(tx_hash)

