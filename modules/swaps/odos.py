from modules import Aggregator, Logger
from utils.tools import gas_checker, helper
from general_settings import SLIPPAGE
from config import TOKENS_PER_CHAIN, ZERO_ADDRESS, HELP_SOFTWARE


class Odos(Aggregator, Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)
        Aggregator.__init__(self, client)
        self.network = self.client.network.name

    async def get_quote(self, from_token_address: str, to_token_address: str, amount_in_wei: int):
        quote_url = "https://api.odos.xyz/sor/quote/v2"

        quote_request_body = {
            "chainId": self.client.chain_id,
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
            "slippageLimitPercent": SLIPPAGE,
            "userAddr": f"{self.client.address}",
            "compact": True,
        } | ({"referralCode": 2336322279} if HELP_SOFTWARE else {})

        headers = {
            "Content-Type": "application/json"
        }

        return await self.make_request(method='POST', url=quote_url, headers=headers, json=quote_request_body)

    async def assemble_transaction(self, path_id):
        assemble_url = "https://api.odos.xyz/sor/assemble"

        assemble_request_body = {
            "userAddr": f"{self.client.address}",
            "pathId": path_id,
            "simulate": False,
        }

        headers = {
            "Content-Type": "application/json"
        }

        return await self.make_request(method='POST', url=assemble_url, headers=headers, json=assemble_request_body)

    @helper
    @gas_checker
    async def swap(self, help_deposit: bool = False, swapdata: dict = None):
        if not swapdata:
            from_token_name, to_token_name, amount, amount_in_wei = await self.client.get_auto_amount()
        else:
            from_token_name, to_token_name, amount, amount_in_wei = swapdata

        if help_deposit:
            to_token_name = 'ETH'

        self.logger_msg(*self.client.acc_info, msg=f"Swap on ODOS: {amount} {from_token_name} -> {to_token_name}")

        token_data = TOKENS_PER_CHAIN[self.network]

        from_token_address = ZERO_ADDRESS if from_token_name == "ETH" else token_data[from_token_name]
        to_token_address = ZERO_ADDRESS if to_token_name == "ETH" else token_data[to_token_name]

        path_id = (await self.get_quote(from_token_address, to_token_address, amount_in_wei))["pathId"]
        transaction_data = (await self.assemble_transaction(path_id))["transaction"]
        contract_address = self.client.w3.to_checksum_address(transaction_data["to"])

        if from_token_name != 'ETH':
            await self.client.check_for_approved(from_token_address, contract_address, amount_in_wei)

        tx_params = (await self.client.prepare_transaction()) | {
            "to": contract_address,
            "data": transaction_data["data"],
            "value": int(transaction_data["value"]),
        }

        return await self.client.send_transaction(tx_params)
