import time

from modules import DEX, Logger
from general_settings import SLIPPAGE
from config import JEDISWAP_CONTRACT, TOKENS_PER_CHAIN
from utils.tools import gas_checker, helper


class JediSwap(DEX, Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)

    async def get_min_amount_out(self, contract_address:int, amount_in_wei: int, path: list):
        min_amount_out = (await self.client.account.client.call_contract(self.client.prepare_call(
            contract_address=contract_address,
            selector_name="get_amounts_out",
            calldata=[amount_in_wei, 0, len(path), *path]
        )))[-2]

        return int(min_amount_out - (min_amount_out / 100 * SLIPPAGE))

    @helper
    @gas_checker
    async def swap(self, swapdata:tuple = None):
        await self.client.initialize_account()

        if swapdata:
            from_token_name, to_token_name, amount, amount_in_wei = swapdata
        else:
            from_token_name, to_token_name, amount, amount_in_wei = await self.client.get_auto_amount()

        self.logger_msg(
            *self.client.acc_info, msg=f'Swap on JediSwap: {amount} {from_token_name} -> {to_token_name}')

        router_contract = JEDISWAP_CONTRACT['router']

        from_token_address = TOKENS_PER_CHAIN[self.client.network.name][from_token_name]
        to_token_address = TOKENS_PER_CHAIN[self.client.network.name][to_token_name]

        deadline = int(time.time()) + 1000000
        path = [from_token_address, to_token_address]
        min_amount_out = await self.get_min_amount_out(router_contract, amount_in_wei, path)

        if to_token_name != 'MEMCOIN':
            await self.client.price_impact_defender(from_token_name, amount, to_token_name, min_amount_out)

        approve_call = self.client.get_approve_call(from_token_address, router_contract, amount_in_wei)

        swap_call = self.client.prepare_call(
            contract_address=router_contract,
            selector_name="swap_exact_tokens_for_tokens",
            calldata=[
                amount_in_wei, 0,
                min_amount_out, 0,
                len(path),
                *path,
                self.client.address,
                deadline
            ]
        )

        return await self.client.send_transaction(approve_call, swap_call)
