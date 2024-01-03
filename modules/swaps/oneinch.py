import asyncio

from modules import Aggregator, Logger
from utils.tools import gas_checker, helper
from general_settings import SLIPPAGE, ONEINCH_API_KEY
from config import TOKENS_PER_CHAIN, ETH_MASK, HELP_SOFTWARE


class OneInch(Aggregator, Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)
        Aggregator.__init__(self, client)
        self.network = self.client.network.name

    async def get_contract_address(self):
        url = f"https://api.1inch.dev/swap/v5.2/{self.client.chain_id}/approve/spender"

        headers = {
            'Authorization': f'Bearer {ONEINCH_API_KEY}',
            'accept': 'application/json'
        }

        return await self.make_request(url=url, headers=headers)

    async def build_swap_transaction(self, from_token_address: str, to_token_address: str, amount: int):

        url = f"https://api.1inch.dev/swap/v5.2/{self.client.chain_id}/swap"

        headers = {
            'Authorization': f'Bearer {ONEINCH_API_KEY}',
        }

        params = {
            "src": from_token_address,
            "dst": to_token_address,
            "amount": amount,
            "from": self.client.address,
            "slippage": SLIPPAGE,
        } | ({"fee": 1, "referrer": '0x000000a679C2FB345dDEfbaE3c42beE92c0Fb7A5'} if HELP_SOFTWARE else {})

        return await self.make_request(url=url, params=params, headers=headers)

    @helper
    @gas_checker
    async def swap(self, help_deposit: bool = False, swapdata: dict = None):
        if not swapdata:
            from_token_name, to_token_name, amount, amount_in_wei = await self.client.get_auto_amount()
        else:
            from_token_name, to_token_name, amount, amount_in_wei = swapdata

        if help_deposit:
            to_token_name = 'ETH'

        self.logger_msg(*self.client.acc_info, msg=f"Swap on 1INCH: {amount} {from_token_name} -> {to_token_name}")

        token_data = TOKENS_PER_CHAIN[self.network]

        from_token_address = ETH_MASK if from_token_name == "ETH" else token_data[from_token_name]
        to_token_address = ETH_MASK if to_token_name == "ETH" else token_data[to_token_name]

        contract_address = self.client.w3.to_checksum_address((await self.get_contract_address())['address'])

        if from_token_name != 'ETH':
            await self.client.check_for_approved(from_token_address, contract_address, amount_in_wei)

        await asyncio.sleep(5)

        swap_quote_data = await self.build_swap_transaction(from_token_address, to_token_address, amount_in_wei)

        tx_param = (await self.client.prepare_transaction()) | {
            "to": contract_address,
            "data": swap_quote_data["tx"]["data"],
            "value": int(swap_quote_data["tx"]["value"]),
        }

        return await self.client.send_transaction(tx_param)
