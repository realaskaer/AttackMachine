from time import time
from modules import DEX
from utils.tools import gas_checker, repeater
from settings import SLIPPAGE
from config import (
    VELOCORE_CONTRACTS,
    VELOCORE_ROUTER_ABI,
    TOKENS_PER_CHAIN, ZERO_ADDRESS
)


class Velocore(DEX):
    def __init__(self, client):
        self.client = client

        self.router_contract = self.client.get_contract(VELOCORE_CONTRACTS['router'], VELOCORE_ROUTER_ABI)

    async def get_min_out(self, from_token_address: str, to_token_address: str, amount_in_wei: int):
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

        from_token_name, to_token_name, amount, amount_in_wei = await self.client.get_auto_amount(class_name='Velocore')

        self.client.logger.info(
            f'{self.client.info} Swap on Velocore: {amount} {from_token_name} -> {to_token_name}')

        token_data = TOKENS_PER_CHAIN[self.client.network.name]

        from_token_address = ZERO_ADDRESS if from_token_name == "ETH" else token_data[from_token_name]
        to_token_address = ZERO_ADDRESS if to_token_name == "ETH" else token_data[to_token_name]

        if from_token_name != 'ETH':
            await self.client.check_for_approved(from_token_address, VELOCORE_CONTRACTS['router'], amount_in_wei)

        tx_params = await self.client.prepare_transaction(value=amount_in_wei if from_token_name == 'ETH' else 0)
        deadline = int(time()) + 1800
        min_amount_out = await self.get_min_out(from_token_address, to_token_address, amount_in_wei)

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
            raise RuntimeError('Velocore interface(UniswapV2) does not support swap Token -> Token')

        return await self.client.send_transaction(transaction)
