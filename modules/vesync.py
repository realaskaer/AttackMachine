from time import time
from modules import DEX
from utils.tools import gas_checker, repeater
from settings import SLIPPAGE_PERCENT
from config import (
    VESYNC_CONTRACTS,
    VESYNC_ROUTER_ABI,
    ZKSYNC_TOKENS
)


class VeSync(DEX):
    def __init__(self, client):
        self.client = client

        self.router_contract = self.client.get_contract(VESYNC_CONTRACTS['router'], VESYNC_ROUTER_ABI)

    async def get_out_data(self, from_token_address: str, to_token_address: str, amount_in_wei: int):
        min_amount_out, pool_stable_type = await self.router_contract.functions.getAmountOut(
            amount_in_wei,
            from_token_address,
            to_token_address
        ).call()
        return int(min_amount_out - (min_amount_out / 100 * SLIPPAGE_PERCENT)), pool_stable_type

    @repeater
    @gas_checker
    async def swap(self):

        from_token_name, to_token_name, amount, amount_in_wei = await self.client.get_auto_amount()

        self.client.logger.info(
            f'{self.client.info} Swap on VeSync: {amount} {from_token_name} -> {to_token_name}')

        from_token_address, to_token_address = ZKSYNC_TOKENS[from_token_name], ZKSYNC_TOKENS[to_token_name]

        if from_token_name != 'ETH':
            await self.client.check_for_approved(from_token_address, VESYNC_CONTRACTS['router'], amount_in_wei)

        tx_params = await self.client.prepare_transaction(amount_in_wei if from_token_name == 'ETH' else 0)
        deadline = int(time()) + 1800
        min_amount_out, pool_stable_type = await self.get_out_data(from_token_address, to_token_address,
                                                                   amount_in_wei)

        await self.client.price_impact_defender(from_token_name, amount, to_token_name, min_amount_out)

        full_data = (
            min_amount_out,
            [
                [
                    from_token_address,
                    to_token_address,
                    pool_stable_type
                ]
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

        tx_hash = await self.client.send_transaction(transaction)

        return await self.client.verify_transaction(tx_hash)
