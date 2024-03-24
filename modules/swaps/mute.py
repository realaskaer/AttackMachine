from time import time
from modules import DEX, Logger
from modules.interfaces import SoftwareException
from utils.tools import gas_checker, helper
from general_settings import SLIPPAGE
from config import (
    MUTE_ROUTER_ABI,
    MUTE_PAIR_DYNAMIC_ABI,
    MUTE_CONTRACTS,
    TOKENS_PER_CHAIN
)


class Mute(DEX, Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)

        self.router_contract = self.client.get_contract(MUTE_CONTRACTS['router'], MUTE_ROUTER_ABI)
        self.pair_contract = self.client.get_contract(MUTE_CONTRACTS['pair_dynamic'], MUTE_PAIR_DYNAMIC_ABI)

    async def get_out_data(self, from_token_address: str, to_token_address: str, amount_in_wei: int):
        min_amount_out, stable_mode, fee = await self.router_contract.functions.getAmountOut(
            amount_in_wei,
            from_token_address,
            to_token_address
        ).call()
        return int(min_amount_out - (min_amount_out / 100 * SLIPPAGE)), stable_mode, fee

    @helper
    @gas_checker
    async def swap(self, help_add_liquidity:bool = False, amount_to_help: float = 0):
        if help_add_liquidity:
            from_token_name = 'ETH'
            to_token_name = 'USDC'
            amount = amount_to_help
            amount_in_wei = self.client.to_wei(amount)
        else:
            from_token_name, to_token_name, amount, amount_in_wei = await self.client.get_auto_amount(class_name='Mute')

        self.logger_msg(*self.client.acc_info, msg=f'Swap on Mute: {amount} {from_token_name} -> {to_token_name}')

        from_token_address, to_token_address = (TOKENS_PER_CHAIN[self.client.network.name][from_token_name],
                                                TOKENS_PER_CHAIN[self.client.network.name][to_token_name])

        deadline = int(time()) + 1800
        min_amount_out, stable_mode, _ = await self.get_out_data(from_token_address, to_token_address, amount_in_wei)

        await self.client.price_impact_defender(from_token_name, amount, to_token_name, min_amount_out)

        if from_token_name != 'ETH':
            await self.client.check_for_approved(from_token_address, MUTE_CONTRACTS['router'], amount_in_wei)

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

        tx_params = await self.client.prepare_transaction(amount_in_wei if from_token_name == 'ETH' else 0)
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

    @helper
    @gas_checker
    async def add_liquidity(self):
        amount, amount_in_wei = await self.client.check_and_get_eth()

        usdc_balance_in_wei, usdc_balance, _ = await self.client.get_token_balance('USDC')
        eth_price = await self.client.get_token_price('ethereum')

        if usdc_balance < (amount / eth_price / 2):
            self.logger_msg(
                *self.client.acc_info, msg=f'Not enough USDC balance, launch {amount} ETH -> USDC swap'
            )
            await self.swap(help_add_liquidity=True, amount_to_help=round(amount / 2 * 1.1, 8))

        amount_in_wei = self.client.to_wei(amount)

        self.logger_msg(*self.client.acc_info, msg=f'Add liquidity to Mute USDC/ETH pool: {amount} ETH')

        amount_eth_min = int(amount_in_wei / 2)

        token_b_address = TOKENS_PER_CHAIN[self.client.network.name]['USDC']

        deadline = int(time()) + 1800
        reserve_token, reserve_eth, _ = await self.pair_contract.functions.getReserves().call()
        amount_token_desired = int(reserve_token * amount_eth_min / reserve_eth)
        amount_token_min = int(amount_token_desired * 0.999)

        fee_type = await self.pair_contract.functions.pairFee().call()
        stable_type = await self.pair_contract.functions.stable().call()

        await self.client.check_for_approved(token_b_address, MUTE_CONTRACTS['router'], amount_token_desired)

        tx_params = await self.client.prepare_transaction(value=amount_eth_min)
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

    @helper
    @gas_checker
    async def withdraw_liquidity(self):
        self.logger_msg(*self.client.acc_info, msg=f'Withdraw liquidity from Mute')

        liquidity_balance = await self.client.get_contract(MUTE_CONTRACTS['pair_dynamic']).functions.balanceOf(
            self.client.address
        ).call()

        if liquidity_balance != 0:

            token_b_address = TOKENS_PER_CHAIN[self.client.network.name]['USDC']

            await self.client.check_for_approved(MUTE_CONTRACTS['pair_dynamic'], MUTE_CONTRACTS['router'], liquidity_balance)

            deadline = int(time()) + 1800
            total_supply = await self.pair_contract.functions.totalSupply().call()
            reserve_token, reserve_eth, _ = await self.pair_contract.functions.getReserves().call()
            min_token_amount_out = int(liquidity_balance * reserve_token / total_supply * 0.999)
            min_eth_amount_out = int(liquidity_balance * reserve_eth / total_supply * 0.999)
            stable_type = await self.pair_contract.functions.stable().call()

            tx_params = await self.client.prepare_transaction()
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
            raise SoftwareException('Insufficient balance on Mute!')
