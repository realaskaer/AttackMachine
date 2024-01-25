from modules import DEX, Logger
from config import MYSWAP_CONTRACT, TOKENS_PER_CHAIN
from modules.interfaces import SoftwareException
from utils.tools import helper, gas_checker
from general_settings import SLIPPAGE


class MySwap(DEX, Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)

    @staticmethod
    async def get_pool_id(from_token_name: str, to_token_name: str):
        pool_data = {
            "ETHUSDC": 1,
            "DAIETH": 2,
            "ETHUSDT": 4,
            "USDCUSDT": 5,
            "DAIUSDC": 6
        }

        pool_id = pool_data.get(from_token_name + to_token_name)

        if pool_id is None:
            pool_id = pool_data.get(to_token_name + from_token_name)
            if pool_id is None:
                raise SoftwareException('This pool is not supported on mySwap')
            else:
                return pool_id, True
        else:
            return pool_id, False

    async def get_min_amount_out(self, contract_address:int, pool_id: int, reverse: bool, amount_in_wei: int):
        pool_data = (await self.client.account.client.call_contract(self.client.prepare_call(
            contract_address=contract_address,
            selector_name="get_pool",
            calldata=[pool_id]
        )))

        reserve_in, reserve_out = (pool_data[5], pool_data[2]) if reverse else (pool_data[2], pool_data[5])
        min_amount_out = reserve_out * amount_in_wei / reserve_in

        return int(min_amount_out - (min_amount_out / 100 * SLIPPAGE))

    @helper
    @gas_checker
    async def swap(self):
        await self.client.initialize_account()

        from_token_name, to_token_name, amount, amount_in_wei = await self.client.get_auto_amount()

        self.logger_msg(*self.client.acc_info, msg=f'Swap on mySwap: {amount} {from_token_name} -> {to_token_name}')

        from_token_address = TOKENS_PER_CHAIN[self.client.network.name][from_token_name]

        router_contract = MYSWAP_CONTRACT['router']

        pool_id, reverse = await self.get_pool_id(from_token_name, to_token_name)
        min_amount_out = await self.get_min_amount_out(router_contract, pool_id, reverse, amount_in_wei)

        await self.client.price_impact_defender(from_token_name, amount, to_token_name, min_amount_out)

        approve_call = self.client.get_approve_call(from_token_address, router_contract, amount_in_wei)

        swap_call = self.client.prepare_call(
            contract_address=router_contract,
            selector_name="swap",
            calldata=[
                pool_id,
                from_token_address,
                amount_in_wei, 0,
                min_amount_out, 0
            ]
        )

        return await self.client.send_transaction(approve_call, swap_call)
