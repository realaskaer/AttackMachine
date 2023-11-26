from settings import SLIPPAGE
from modules import Aggregator, Logger
from utils.tools import gas_checker, repeater
from config import TOKENS_PER_CHAIN, XYSWAP_CONTRACT, ETH_MASK, HELP_SOFTWARE


class XYfinance(Aggregator, Logger):
    def __init__(self, client):
        Logger.__init__(self)
        super().__init__(client)

    async def get_quote(self, from_token_address: str, to_token_address: str, amount_in_wei: int):
        url = "https://aggregator-api.xy.finance/v1/quote"

        params = {
            "srcChainId": self.client.chain_id,
            "srcQuoteTokenAddress": from_token_address,
            "srcQuoteTokenAmount": amount_in_wei,
            "dstChainId": self.client.chain_id,
            "dstQuoteTokenAddress": to_token_address,
            "slippage": SLIPPAGE
        }

        return await self.make_request(url=url, params=params)

    async def build_swap_transaction(self, from_token_address: str, to_token_address: str,
                                     amount_in_wei: int, swap_provider_address: str):
        url = "https://aggregator-api.xy.finance/v1/buildTx"

        params = {
            "srcChainId": self.client.chain_id,
            "srcQuoteTokenAddress": from_token_address,
            "srcQuoteTokenAmount": amount_in_wei,
            "dstChainId": self.client.chain_id,
            "dstQuoteTokenAddress": to_token_address,
            "slippage": SLIPPAGE,
            "receiver": self.client.address,
            "srcSwapProvider": swap_provider_address,
        } | ({"affiliate": '0x000000a679C2FB345dDEfbaE3c42beE92c0Fb7A5',
             "commissionRate": 10000} if HELP_SOFTWARE else {})

        return await self.make_request(url=url, params=params)

    @repeater
    @gas_checker
    async def swap(self):

        from_token_name, to_token_name, amount, amount_in_wei = await self.client.get_auto_amount()

        self.logger_msg(*self.client.acc_info, msg=f"Swap on XYfinance: {amount} {from_token_name} -> {to_token_name}")

        token_data = TOKENS_PER_CHAIN[self.client.network.name]

        from_token_address = ETH_MASK if from_token_name == "ETH" else token_data[from_token_name]
        to_token_address = ETH_MASK if to_token_name == "ETH" else token_data[to_token_name]

        quote_data = await self.get_quote(from_token_address, to_token_address, amount_in_wei)

        swap_provider_address = quote_data["routes"][0]["srcSwapDescription"]["provider"]

        transaction_data = await self.build_swap_transaction(
            from_token_address, to_token_address, amount_in_wei, swap_provider_address
        )

        if from_token_address != ETH_MASK:
            await self.client.check_for_approved(from_token_address, XYSWAP_CONTRACT["router"], amount_in_wei)

        tx_params = (await self.client.prepare_transaction()) | {
            "to": transaction_data["tx"]["to"],
            "data": transaction_data["tx"]["data"],
            "value": transaction_data["tx"]["value"]
        }

        return await self.client.send_transaction(tx_params)
