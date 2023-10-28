import aiohttp

from settings import SLIPPAGE_PERCENT
from modules import Client
from utils.tools import gas_checker, repeater
from config import ZKSYNC_TOKENS, XYSWAP_CONTRACT, ETH_MASK, HELP_SOFTWARE


class XYfinance(Client):
    def __init__(self, account_number, private_key, network, proxy=None):
        super().__init__(account_number, private_key, network, proxy)

    async def get_quote(self, from_token_address: str, to_token_address: str, amount_in_wei: int):
        url = "https://aggregator-api.xy.finance/v1/quote"

        params = {
            "srcChainId": self.chain_id,
            "srcQuoteTokenAddress": from_token_address,
            "srcQuoteTokenAmount": amount_in_wei,
            "dstChainId": self.chain_id,
            "dstQuoteTokenAddress": to_token_address,
            "slippage": SLIPPAGE_PERCENT
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, params=params, proxy=self.proxy) as response:
                if response.status == 200:
                    return await response.json()
                raise RuntimeError(f"Bad request to XYfinance API: {response.status}")

    async def build_swap_transaction(self, from_token_address: str, to_token_address: str,
                                     amount_in_wei: int, swap_provider_address: str):
        url = "https://aggregator-api.xy.finance/v1/buildTx"

        params = {
            "srcChainId": self.chain_id,
            "srcQuoteTokenAddress": from_token_address,
            "srcQuoteTokenAmount": amount_in_wei,
            "dstChainId": self.chain_id,
            "dstQuoteTokenAddress": to_token_address,
            "slippage": SLIPPAGE_PERCENT,
            "receiver": self.address,
            "srcSwapProvider": swap_provider_address,
        } | {"affiliate": '0x000000a679C2FB345dDEfbaE3c42beE92c0Fb7A5',
             "commissionRate": 10000} if HELP_SOFTWARE else {}

        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, params=params, proxy=self.proxy) as response:
                if response.status == 200:
                    return await response.json()
                raise RuntimeError(f"Bad request to XYfinance API: {response.status}")

    @repeater
    @gas_checker
    async def swap(self):

        from_token_name, to_token_name, amount, amount_in_wei = await self.get_auto_amount()

        self.logger.info(f'{self.info} Swap on XYfinance: {amount} {from_token_name} -> {to_token_name}')

        from_token_address = ETH_MASK if from_token_name == "ETH" else ZKSYNC_TOKENS[from_token_name]
        to_token_address = ETH_MASK if to_token_name == "ETH" else ZKSYNC_TOKENS[to_token_name]

        quote_data = await self.get_quote(from_token_address, to_token_address, amount_in_wei)

        swap_provider_address = quote_data["routes"][0]["srcSwapDescription"]["provider"]

        transaction_data = await self.build_swap_transaction(
            from_token_address, to_token_address, amount_in_wei, swap_provider_address
        )

        if from_token_address != ETH_MASK:
            await self.check_for_approved(from_token_address, XYSWAP_CONTRACT["router"], amount_in_wei)

        tx_params = (await self.prepare_transaction()) | {
            "to": transaction_data["tx"]["to"],
            "data": transaction_data["tx"]["data"],
            "value": transaction_data["tx"]["value"]
        }

        tx_hash = await self.send_transaction(tx_params)

        await self.verify_transaction(tx_hash)
