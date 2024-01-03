from config import AVNU_CONTRACT, TOKENS_PER_CHAIN, HELP_SOFTWARE
from utils.tools import helper, gas_checker
from general_settings import SLIPPAGE
from modules import Aggregator, Logger


class AVNU(Aggregator, Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)
        Aggregator.__init__(self, client)

    async def get_quotes(self, from_token_address: int, to_token_address: int, amount_in_wei: int):
        url = "https://starknet.api.avnu.fi/swap/v1/quotes"

        params = {
            "sellTokenAddress": hex(from_token_address),
            "buyTokenAddress": hex(to_token_address),
            "sellAmount": hex(amount_in_wei),
        } | ({
                "integratorFees": hex(100),
                "integratorFeeRecipient": hex(0x04FaFe3DC5005a717bB905c10108afD23691a70b53772525503f4b0979712816)
        } if HELP_SOFTWARE else {})

        return (await self.make_request(method='GET', url=url, params=params))[0]["quoteId"]

    async def build_transaction(self, quote_id: str):
        url = "https://starknet.api.avnu.fi/swap/v1/build"

        data = {
            "quoteId": quote_id,
            "takerAddress": hex(self.client.address),
            "slippage": float(SLIPPAGE / 100),
        }

        return await self.make_request(method='POST', url=url, json=data)

    @helper
    @gas_checker
    async def swap(self, help_deposit: bool = False, swapdata: dict = None):
        await self.client.initialize_account()

        if not swapdata:
            from_token_name, to_token_name, amount, amount_in_wei = await self.client.get_auto_amount()
        else:
            from_token_name, to_token_name, amount, amount_in_wei = swapdata

        if help_deposit:
            to_token_name = 'ETH'

        self.logger_msg(*self.client.acc_info, msg=f"Swap on AVNU: {amount} {from_token_name} -> {to_token_name}")

        from_token_address = TOKENS_PER_CHAIN[self.client.network.name][from_token_name]
        to_token_address = TOKENS_PER_CHAIN[self.client.network.name][to_token_name]

        quote_id = await self.get_quotes(from_token_address, to_token_address, amount_in_wei)
        transaction_data = await self.build_transaction(quote_id)

        approve_call = self.client.get_approve_call(from_token_address,  AVNU_CONTRACT["router"], amount_in_wei)

        calldata = list(map(lambda x: int(x, 16), transaction_data["calldata"]))

        swap_call = self.client.prepare_call(AVNU_CONTRACT["router"], transaction_data["entrypoint"], calldata)

        return await self.client.send_transaction(approve_call, swap_call)
