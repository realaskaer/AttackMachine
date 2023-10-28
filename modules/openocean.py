import aiohttp

from modules import Client
from utils.tools import gas_checker, repeater
from settings import SLIPPAGE_PERCENT
from config import OPENOCEAN_CONTRACT, ZKSYNC_TOKENS, ETH_MASK, HELP_SOFTWARE


class OpenOcean(Client):
    async def build_swap_transaction(self, from_token_address: str, to_token_address: str, amount: float):

        url = f'https://open-api.openocean.finance/v3/{self.chain_id}/swap_quote'

        params = {
            'chain': self.chain_id,
            'inTokenAddress': from_token_address,
            'outTokenAddress': to_token_address,
            'amount': amount,
            'gasPrice': str(self.w3.from_wei(await self.w3.eth.gas_price, 'gwei')),
            'slippage': SLIPPAGE_PERCENT,
            'account': self.address
        } | {'referrer': '0x000000a679C2FB345dDEfbaE3c42beE92c0Fb7A5', 'referrerFee': 1} if HELP_SOFTWARE else {}

        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, params=params, proxy=self.proxy) as response:
                if response.status == 200:
                    return await response.json()
                raise RuntimeError(f"Bad request to OpenOcean API: {response.status}")

    @repeater
    @gas_checker
    async def swap(self):

        from_token_name, to_token_name, amount, amount_in_wei = await self.get_auto_amount()

        self.logger.info(f'{self.info} Swap on OpenOcean: {amount} {from_token_name} -> {to_token_name}')

        from_token_address = ETH_MASK if from_token_name == "ETH" else ZKSYNC_TOKENS[from_token_name]
        to_token_address = ETH_MASK if to_token_name == "ETH" else ZKSYNC_TOKENS[to_token_name]

        swap_quote_data = await self.build_swap_transaction(from_token_address, to_token_address, amount)

        if from_token_address != ETH_MASK:
            await self.check_for_approved(from_token_address, OPENOCEAN_CONTRACT["router"], amount_in_wei)

        tx_params = (await self.prepare_transaction()) | {
            "to": swap_quote_data["data"]["to"],
            "data": swap_quote_data["data"]["data"],
            "value": int(swap_quote_data["data"]["value"])
        }

        tx_hash = await self.send_transaction(tx_params)

        await self.verify_transaction(tx_hash)
