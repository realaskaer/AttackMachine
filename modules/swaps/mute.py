from time import time
from modules import DEX
from utils.tools import gas_checker, repeater
from settings import SLIPPAGE
from config import (
    MUTE_ROUTER_ABI,
    MUTE_PAIR_DYNAMIC_ABI,
    MUTE_CONTRACTS,
    TOKENS_PER_CHAIN
)


class Mute(DEX):
    def __init__(self, client):
        self.client = client

        self.router_contract = self.client.get_contract(MUTE_CONTRACTS['router'], MUTE_ROUTER_ABI)
        self.pair_contract = self.client.get_contract(MUTE_CONTRACTS['pair_dynamic'], MUTE_PAIR_DYNAMIC_ABI)

    async def get_out_data(self, from_token_address: str, to_token_address: str, amount_in_wei: int):
        min_amount_out, stable_mode, fee = await self.router_contract.functions.getAmountOut(
            amount_in_wei,
            from_token_address,
            to_token_address
        ).call()
        return int(min_amount_out - (min_amount_out / 100 * SLIPPAGE)), stable_mode, fee

    @repeater
    @gas_checker
    async def swap(self, help_add_liquidity:bool = False, amount_to_help: float = 0):

        if help_add_liquidity:
            from_token_name = 'ETH'
            to_token_name = 'USDC'
            amount = amount_to_help
            amount_in_wei = int(amount_to_help * 10 ** 18)
        else:
            from_token_name, to_token_name, amount, amount_in_wei = await self.client.get_auto_amount(class_name='Mute')

        self.client.logger.info(
            f'{self.client.info} Swap on Mute: {amount} {from_token_name} -> {to_token_name}')

        from_token_address, to_token_address = (TOKENS_PER_CHAIN[self.client.network.name][from_token_name],
                                                TOKENS_PER_CHAIN[self.client.network.name][to_token_name])

        if from_token_name != 'ETH':
            await self.client.check_for_approved(from_token_address, MUTE_CONTRACTS['router'], amount_in_wei)

        tx_params = await self.client.prepare_transaction(amount_in_wei if from_token_name == 'ETH' else 0)
        deadline = int(time()) + 1800
        min_amount_out, stable_mode, _ = await self.get_out_data(from_token_address, to_token_address, amount_in_wei)

        await self.client.price_impact_defender(from_token_name, amount, to_token_name, min_amount_out)

        full_data = (
            min_amount_out,
            [
                from_token_address,
                to_token_address
            ],
            self.client.address,
            deadline,
            [stable_mode]
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

    @repeater
    @gas_checker
    async def add_liquidity(self):

        amount_from_settings, amount_from_settings_in_wei = await self.client.check_and_get_eth_for_liquidity()

        usdc_balance_in_wei, usdc_balance, _ = await self.client.get_token_balance('USDC')

        if usdc_balance < (amount_from_settings / 2):
            await self.swap(help_add_liquidity=True, amount_to_help=round(amount_from_settings / 2 * 1.1, 8))

        amount_from_settings_in_wei = amount_from_settings * 10 ** 18

        self.client.logger.info(
            f'{self.client.info} Add liquidity to Mute USDC/ETH pool: {amount_from_settings} ETH')

        amount_eth_min = int(amount_from_settings_in_wei / 2)

        token_b_address = TOKENS_PER_CHAIN[self.client.network.name]['USDC']

        tx_params = await self.client.prepare_transaction(value=amount_eth_min)
        deadline = int(time()) + 1800

        reserve_token, reserve_eth, _ = await self.pair_contract.functions.getReserves().call()
        amount_token_desired = int(reserve_token * amount_eth_min / reserve_eth)
        amount_token_min = int(amount_token_desired * 0.999)

        fee_type = await self.pair_contract.functions.pairFee().call()
        stable_type = await self.pair_contract.functions.stable().call()

        await self.client.check_for_approved(token_b_address, MUTE_CONTRACTS['router'], amount_token_desired)

        transaction = await self.router_contract.functions.addLiquidityETH(
            token_b_address,
            amount_token_desired,
            amount_token_min,
            int(amount_eth_min * 0.999),
            self.client.address,
            deadline,
            fee_type,
            stable_type
        ).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)

    @repeater
    @gas_checker
    async def withdraw_liquidity(self):
        self.client.logger.info(f'{self.client.info} Withdraw liquidity from Mute')

        liquidity_balance = await self.client.get_contract(MUTE_CONTRACTS['pair_dynamic']).functions.balanceOf(
            self.client.address
        ).call()

        if liquidity_balance != 0:

            token_b_address = TOKENS_PER_CHAIN[self.client.network.name]['USDC']

            await self.client.check_for_approved(MUTE_CONTRACTS['pair_dynamic'], MUTE_CONTRACTS['router'], liquidity_balance)

            tx_params = await self.client.prepare_transaction()
            deadline = int(time()) + 1800

            total_supply = await self.pair_contract.functions.totalSupply().call()
            reserve_token, reserve_eth, _ = await self.pair_contract.functions.getReserves().call()
            min_token_amount_out = int(liquidity_balance * reserve_token / total_supply * 0.999)
            min_eth_amount_out = int(liquidity_balance * reserve_eth / total_supply * 0.999)
            stable_type = await self.pair_contract.functions.stable().call()

            transaction = await self.router_contract.functions.removeLiquidityETHSupportingFeeOnTransferTokens(
                token_b_address,
                liquidity_balance,
                min_token_amount_out,
                min_eth_amount_out,
                self.client.address,
                deadline,
                stable_type
            ).build_transaction(tx_params)

            return await self.client.send_transaction(transaction)

        else:
            raise RuntimeError('Insufficient balance on Mute!')
