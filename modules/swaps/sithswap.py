import time

from modules import DEX, Logger
from config import SITHSWAP_CONTRACT, TOKENS_PER_CHAIN
from utils.tools import helper, gas_checker
from general_settings import SLIPPAGE


class SithSwap(DEX, Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)

    @staticmethod
    async def get_min_amount_out(contract, amount_in_wei: int, from_token_address: str, to_token_address: str):
        min_amount_out, stable_type = await contract.functions["getAmountOut"].prepare(
            amount_in_wei,
            from_token_address,
            to_token_address
        ).call()

        return int(min_amount_out - (min_amount_out / 100 * SLIPPAGE)), stable_type

    @helper
    @gas_checker
    async def swap(self):
        await self.client.initialize_account()

        from_token_name, to_token_name, amount, amount_in_wei = await self.client.get_auto_amount()

        self.logger_msg(
            *self.client.acc_info, msg=f'Swap on SithSwap: {amount} {from_token_name} -> {to_token_name}')

        router_contract = await self.client.get_contract(contract_address=SITHSWAP_CONTRACT['router'])

        from_token_address = TOKENS_PER_CHAIN[self.client.network.name][from_token_name]
        to_token_address = TOKENS_PER_CHAIN[self.client.network.name][to_token_name]

        deadline = int(time.time()) + 1000000
        min_amount_out, stable_type = await self.get_min_amount_out(router_contract, amount_in_wei,
                                                                    from_token_address, to_token_address)
        route = [
            {
                "from_address": from_token_address,
                "to_address": to_token_address,
                "stable": stable_type
            }
        ]

        await self.client.price_impact_defender(from_token_name, amount, to_token_name, min_amount_out)

        approve_call = self.client.get_approve_call(from_token_address, SITHSWAP_CONTRACT['router'], amount_in_wei)

        swap_call = router_contract.functions["swapExactTokensForTokens"].prepare(
            amount_in_wei,
            min_amount_out,
            route,
            self.client.address,
            deadline
        )

        return await self.client.send_transaction(approve_call, swap_call)
