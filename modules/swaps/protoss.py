import time

from modules import DEX, Logger
from config import PROTOSS_CONTRACT, TOKENS_PER_CHAIN
from utils.tools import gas_checker, helper
from general_settings import SLIPPAGE


class Protoss(DEX, Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)

    @staticmethod
    async def get_min_amount_out(contract, amount_in_wei: int, path: tuple):
        min_amount_out = (await contract.functions["getAmountsOut"].prepare(
            amount_in_wei,
            path
        ).call()).amounts[1]

        return int(min_amount_out - (min_amount_out / 100 * SLIPPAGE))

    @helper
    @gas_checker
    async def swap(self):
        await self.client.initialize_account()

        from_token_name, to_token_name, amount, amount_in_wei = await self.client.get_auto_amount()

        self.logger_msg(
            *self.client.acc_info, msg=f'Swap on Protoss: {amount} {from_token_name} -> {to_token_name}')

        router_contract = await self.client.get_contract(contract_address=PROTOSS_CONTRACT['router'])

        from_token_address = TOKENS_PER_CHAIN[self.client.network.name][from_token_name]
        to_token_address = TOKENS_PER_CHAIN[self.client.network.name][to_token_name]

        deadline = int(time.time()) + 1000000
        path = from_token_address, to_token_address
        min_amount_out = await self.get_min_amount_out(router_contract, amount_in_wei, path)

        await self.client.price_impact_defender(from_token_name, amount, to_token_name, min_amount_out)

        approve_call = self.client.get_approve_call(from_token_address, PROTOSS_CONTRACT['router'], amount_in_wei)

        swap_call = router_contract.functions["swapExactTokensForTokens"].prepare(
            amount_in_wei,
            min_amount_out,
            path,
            self.client.address,
            deadline
        )

        return await self.client.send_transaction(approve_call, swap_call)
