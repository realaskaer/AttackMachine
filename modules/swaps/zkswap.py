from time import time
from utils.tools import gas_checker, repeater
from settings import SLIPPAGE
from modules import DEX, Logger
from config import (
    ZKSWAP_CONTRACTS,
    ZKSWAP_ROUTER_ABI,
    TOKENS_PER_CHAIN
)


class ZkSwap(DEX, Logger):
    def __init__(self, client):
        super().__init__()
        self.client = client

        self.router_contract = self.client.get_contract(ZKSWAP_CONTRACTS['router'], ZKSWAP_ROUTER_ABI)

    async def get_min_amount_out(self, from_token_address: str, to_token_address: str, amount_in_wei: int):
        _, min_amount_out = await self.router_contract.functions.getAmountsOut(
            amount_in_wei,
            [
                from_token_address,
                to_token_address
            ]
        ).call()

        return int(min_amount_out - (min_amount_out / 100 * SLIPPAGE))

    @repeater
    @gas_checker
    async def swap(self):

        from_token_name, to_token_name, amount, amount_in_wei = await self.client.get_auto_amount()

        self.logger_msg(*self.client.acc_info, msg=f'Swap on zkSwap: {amount} {from_token_name} -> {to_token_name}')

        from_token_address = TOKENS_PER_CHAIN[self.client.network.name][from_token_name]
        to_token_address = TOKENS_PER_CHAIN[self.client.network.name][to_token_name]

        if from_token_name != 'ETH':
            await self.client.check_for_approved(from_token_address, ZKSWAP_CONTRACTS['router'], amount_in_wei)

        tx_params = await self.client.prepare_transaction()
        tx_params['value'] = amount_in_wei if from_token_name == 'ETH' else 0
        deadline = int(time()) + 1800
        min_amount_out = await self.get_min_amount_out(from_token_address, to_token_address, amount_in_wei)

        await self.client.price_impact_defender(from_token_name, amount, to_token_name, min_amount_out)

        full_data = (
            min_amount_out,
            [
                from_token_address,
                to_token_address
            ],
            self.client.address,
            deadline
        )

        if from_token_name == 'ETH':
            transaction = await self.router_contract.functions.swapExactETHForTokens(
                *full_data
            ).build_transaction(tx_params)
        elif to_token_name == 'ETH':
            transaction = await self.router_contract.functions.swapExactTokensForETH(
                amount_in_wei,
                *full_data
            ).build_transaction(tx_params)
        else:
            transaction = await self.router_contract.functions.swapExactTokensForTokens(
                amount_in_wei,
                *full_data
            ).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)
