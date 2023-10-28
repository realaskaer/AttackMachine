import aiohttp

from modules import Client
from utils.tools import gas_checker, repeater
from settings import SLIPPAGE_PERCENT, ONEINCH_API_KEY
from config import ONEINCH_CONTRACT, ZKSYNC_TOKENS, ETH_MASK, HELP_SOFTWARE


class OneInch(Client):
    async def build_swap_transaction(self, from_token_address: str, to_token_address: str, amount: int):

        url = f"https://api.1inch.dev/swap/v5.2/{await self.w3.eth.chain_id}/swap"

        headers = {
            'Authorization': f'Bearer {ONEINCH_API_KEY}',
            'accept': 'application/json'}

        params = {
            "src": from_token_address,
            "dst": to_token_address,
            "amount": amount,
            "from": self.address,
            "slippage": SLIPPAGE_PERCENT,
        } | {"referrer": '0x000000a679C2FB345dDEfbaE3c42beE92c0Fb7A5', "fee": 1} if HELP_SOFTWARE else {}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, proxy=self.proxy) as response:
                data = await response.json()
                if response.status == 200:
                    return data
                raise RuntimeError(f"Bad request to 1INCH API: {response.status}")

    @repeater
    @gas_checker
    async def swap(self, help_add_liquidity:bool = False, amount_to_help:int = 0):

        from_token_name, to_token_name, amount, amount_in_wei = await self.get_auto_amount()

        if help_add_liquidity:
            to_token_name = 'ETH'
            decimals = 18 if from_token_name == 'BUSD' else 6
            eth_price = await self.get_token_price('ethereum')

            amount = round(amount_to_help * eth_price, 4)
            amount_in_wei = int(amount * 10 ** decimals)

        self.logger.info(f'{self.info} Swap on 1INCH: {amount} {from_token_name} -> {to_token_name}')

        from_token_address = ETH_MASK if from_token_name == "ETH" else ZKSYNC_TOKENS[from_token_name]
        to_token_address = ETH_MASK if to_token_name == "ETH" else ZKSYNC_TOKENS[to_token_name]

        if from_token_address != ETH_MASK:
            await self.check_for_approved(from_token_address, ONEINCH_CONTRACT["router"], amount_in_wei)

        swap_quote_data = await self.build_swap_transaction(from_token_address, to_token_address, amount_in_wei)

        tx_param = (await self.prepare_transaction()) | {
            "to": self.w3.to_checksum_address(swap_quote_data["tx"]["to"]),
            "data": swap_quote_data["tx"]["data"],
            "value": int(swap_quote_data["tx"]["value"]),
        }

        tx_hash = await self.send_transaction(tx_param)

        await self.verify_transaction(tx_hash)
