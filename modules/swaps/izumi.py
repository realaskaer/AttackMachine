from time import time
from modules import DEX, Logger
from utils.tools import gas_checker, helper
from general_settings import SLIPPAGE
from hexbytes import HexBytes
from config import (
    TOKENS_PER_CHAIN,
    IZUMI_QUOTER_ABI,
    IZUMI_ROUTER_ABI,
    IZUMI_CONTRACTS,
    ZERO_ADDRESS
)


class Izumi(DEX, Logger):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.network = self.client.network.name
        self.router_contract = self.client.get_contract(IZUMI_CONTRACTS[self.network]['router'], IZUMI_ROUTER_ABI)
        self.quoter_contract = self.client.get_contract(IZUMI_CONTRACTS[self.network]['quoter'], IZUMI_QUOTER_ABI)

    @staticmethod
    def get_path(from_token_address: str, to_token_address: str, fee:int):
        from_token_bytes = HexBytes(from_token_address).rjust(20, b'\0')
        to_token_bytes = HexBytes(to_token_address).rjust(20, b'\0')
        fee_bytes = fee.to_bytes(3, 'big')

        return from_token_bytes + fee_bytes + to_token_bytes

    async def get_min_amount_out(self, path: bytes, amount_in_wei: int):
        min_amount_out, _ = await self.quoter_contract.functions.swapAmount(
            amount_in_wei,
            path
        ).call()

        return int(min_amount_out - (min_amount_out / 100 * SLIPPAGE))

    async def get_pool_fee(self, from_token_address:str, to_token_address:str, fee:int = 400):
        pool_address = await self.quoter_contract.functions.pool(
            from_token_address,
            to_token_address,
            fee
        ).call()
        if pool_address != ZERO_ADDRESS:
            return fee
        return await self.get_pool_fee(from_token_address, to_token_address, fee=500)

    @helper
    @gas_checker
    async def swap(self):
        from_token_name, to_token_name, amount, amount_in_wei = await self.client.get_auto_amount(class_name='Izumi')

        self.logger_msg(*self.client.acc_info, msg=f'Swap on Izumi: {amount} {from_token_name} -> {to_token_name}')

        from_token_address, to_token_address = (TOKENS_PER_CHAIN[self.network][from_token_name],
                                                TOKENS_PER_CHAIN[self.network][to_token_name])

        deadline = int(time()) + 1800
        pool_fee = await self.get_pool_fee(from_token_address, to_token_address)
        path = self.get_path(from_token_address, to_token_address, pool_fee)
        min_amount_out = await self.get_min_amount_out(path, amount_in_wei)

        await self.client.price_impact_defender(from_token_name, amount, to_token_name, min_amount_out)

        if from_token_name != 'ETH':
            await self.client.check_for_approved(
                from_token_address, IZUMI_CONTRACTS[self.network]['router'], amount_in_wei
            )

        tx_data = self.router_contract.encodeABI(
            fn_name='swapAmount',
            args=[(
                path,
                self.client.address if to_token_name != 'ETH' else ZERO_ADDRESS,
                amount_in_wei,
                min_amount_out,
                deadline
            )]
        )

        full_data = [tx_data]

        if from_token_name == 'ETH' or to_token_name == 'ETH':
            tx_additional_data = self.router_contract.encodeABI(
                fn_name='unwrapWETH9' if from_token_name != 'ETH' else 'refundETH',
                args=[
                    min_amount_out,
                    self.client.address
                ] if from_token_name != 'ETH' else None
            )
            full_data.append(tx_additional_data)

        tx_params = await self.client.prepare_transaction(value=amount_in_wei if from_token_name == 'ETH' else 0)
        transaction = await self.router_contract.functions.multicall(
            full_data
        ).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)
