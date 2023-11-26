from modules import Aggregator, Logger
from utils.tools import gas_checker, repeater
from settings import SLIPPAGE, ONEINCH_API_KEY
from config import ONEINCH_CONTRACT, TOKENS_PER_CHAIN, ETH_MASK, HELP_SOFTWARE


class OneInch(Aggregator, Logger):
    def __init__(self, client):
        Logger.__init__(self)
        super().__init__(client)

    async def build_swap_transaction(self, from_token_address: str, to_token_address: str, amount: int):

        url = f"https://api.1inch.dev/swap/v5.2/{self.client.chain_id}/swap"

        headers = {
            'Authorization': f'Bearer {ONEINCH_API_KEY}',
            'accept': 'application/json'}

        params = {
            "src": from_token_address,
            "dst": to_token_address,
            "amount": amount,
            "from": self.client.address,
            "slippage": SLIPPAGE,
        } | ({"referrer": '0x000000a679C2FB345dDEfbaE3c42beE92c0Fb7A5', "fee": 1} if HELP_SOFTWARE else {})

        return await self.make_request(url=url, params=params, headers=headers)

    @repeater
    @gas_checker
    async def swap(self, help_add_liquidity:bool = False, amount_to_help:int = 0):

        from_token_name, to_token_name, amount, amount_in_wei = await self.client.get_auto_amount()

        if help_add_liquidity:
            to_token_name = 'ETH'
            decimals = 18 if from_token_name == 'BUSD' else 6
            eth_price = await self.client.get_token_price('ethereum')

            amount = round(amount_to_help * eth_price, 4)
            amount_in_wei = int(amount * 10 ** decimals)

        self.logger_msg(*self.client.acc_info, msg=f"Swap on 1INCH: {amount} {from_token_name} -> {to_token_name}")

        token_data = TOKENS_PER_CHAIN[self.client.network.name]

        from_token_address = ETH_MASK if from_token_name == "ETH" else token_data[from_token_name]
        to_token_address = ETH_MASK if to_token_name == "ETH" else token_data[to_token_name]

        if from_token_address != ETH_MASK:
            await self.client.check_for_approved(from_token_address, ONEINCH_CONTRACT["router"], amount_in_wei)

        swap_quote_data = await self.build_swap_transaction(from_token_address, to_token_address, amount_in_wei)

        tx_param = (await self.client.prepare_transaction()) | {
            "to": self.client.w3.to_checksum_address(swap_quote_data["tx"]["to"]),
            "data": swap_quote_data["tx"]["data"],
            "value": int(swap_quote_data["tx"]["value"]),
        }

        return await self.client.send_transaction(tx_param)
