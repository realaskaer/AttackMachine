from time import time
from eth_abi import abi
from modules import DEX, Logger
from utils.tools import gas_checker, helper
from general_settings import SLIPPAGE
from config import (
    SYNCSWAP_CONTRACTS,
    SYNCSWAP_CLASSIC_POOL_FACTORY_ABI,
    SYNCSWAP_CLASSIC_POOL_ABI,
    SYNCSWAP_ROUTER_ABI,
    ZERO_ADDRESS,
    TOKENS_PER_CHAIN
)


class SyncSwap(DEX, Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)
        self.network = self.client.network.name
        self.router_contract = self.client.get_contract(
            SYNCSWAP_CONTRACTS[self.network]['router'],
            SYNCSWAP_ROUTER_ABI)
        self.pool_factory_contract = self.client.get_contract(
            SYNCSWAP_CONTRACTS[self.network]['classic_pool_factoty'],
            SYNCSWAP_CLASSIC_POOL_FACTORY_ABI
        )

    async def get_min_amount_out(self, pool_address: str, from_token_address: str, amount_in_wei: int):
        pool_contract = self.client.get_contract(pool_address, SYNCSWAP_CLASSIC_POOL_ABI)
        min_amount_out = await pool_contract.functions.getAmountOut(
            from_token_address,
            amount_in_wei,
            self.client.address
        ).call()

        return int(min_amount_out - (min_amount_out / 100 * SLIPPAGE))

    @helper
    @gas_checker
    async def swap(self):
        try:
            from_token_name, to_token_name, amount, amount_in_wei = await self.client.get_auto_amount()

            self.logger_msg(*self.client.acc_info, msg=f'Swap on SyncSwap: {amount} {from_token_name} -> {to_token_name}')

            from_token_address = TOKENS_PER_CHAIN[self.network][from_token_name]
            to_token_address = TOKENS_PER_CHAIN[self.network][to_token_name]

            withdraw_mode = 1
            pool_address = await self.pool_factory_contract.functions.getPool(from_token_address,
                                                                              to_token_address).call()
            deadline = int(time()) + 1800
            min_amount_out = await self.get_min_amount_out(pool_address, from_token_address, amount_in_wei)

            await self.client.price_impact_defender(from_token_name, amount, to_token_name, min_amount_out)

            if from_token_name != 'ETH':
                await self.client.check_for_approved(
                    from_token_address, SYNCSWAP_CONTRACTS[self.network]['router'], amount_in_wei
                )

            swap_data = abi.encode(['address', 'address', 'uint8'],
                                   [from_token_address, self.client.address, withdraw_mode])

            steps = [{
                'pool': pool_address,
                'data': swap_data,
                'callback': ZERO_ADDRESS,
                'callbackData': '0x'
            }]

            paths = [{
                'steps': steps,
                'tokenIn': from_token_address if from_token_name != 'ETH' else ZERO_ADDRESS,
                'amountIn': amount_in_wei
            }]

            tx_params = await self.client.prepare_transaction(value=amount_in_wei if from_token_name == 'ETH' else 0)
            transaction = await self.router_contract.functions.swap(
                paths,
                min_amount_out,
                deadline,
            ).build_transaction(tx_params)

            return await self.client.send_transaction(transaction)
        finally:
            await self.client.session.close()

    @helper
    @gas_checker
    async def add_liquidity(self):
        try:
            amount, amount_in_wei = await self.client.check_and_get_eth()

            self.logger_msg(
                *self.client.acc_info, msg=f'Add liquidity to SyncSwap USDC/ETH pool: {amount} ETH')

            token_a_address = TOKENS_PER_CHAIN[self.client.network.name]['ETH']
            token_b_address = TOKENS_PER_CHAIN[self.client.network.name]['USDC']

            pool_address = await self.pool_factory_contract.functions.getPool(token_a_address, token_b_address).call()
            pool_contract = self.client.get_contract(pool_address, SYNCSWAP_CLASSIC_POOL_ABI)

            total_supply = await pool_contract.functions.totalSupply().call()
            _, reserve_eth = await pool_contract.functions.getReserves().call()
            # fee = await pool_contract.functions.getProtocolFee().call()
            min_lp_amount_out = int(amount_in_wei * total_supply / reserve_eth / 2 * 0.9965)

            inputs = [
                (token_b_address, 0),
                (ZERO_ADDRESS, amount_in_wei)
            ]

            tx_params = await self.client.prepare_transaction(value=amount_in_wei)
            transaction = await self.router_contract.functions.addLiquidity2(
                pool_address,
                inputs,
                abi.encode(['address'], [self.client.address]),
                min_lp_amount_out,
                ZERO_ADDRESS,
                '0x'
            ).build_transaction(tx_params)

            return await self.client.verify_transaction(transaction)
        finally:
            await self.client.session.close()

    @helper
    @gas_checker
    async def withdraw_liquidity(self):
        self.logger_msg(*self.client.acc_info, msg=f'Withdraw liquidity from SyncSwap')

        token_a_address = TOKENS_PER_CHAIN[self.client.network.name]['ETH']
        token_b_address = TOKENS_PER_CHAIN[self.client.network.name]['USDC']

        pool_address = await self.pool_factory_contract.functions.getPool(token_a_address, token_b_address).call()
        pool_contract = self.client.get_contract(pool_address, SYNCSWAP_CLASSIC_POOL_ABI)

        liquidity_balance = await pool_contract.functions.balanceOf(self.client.address).call()

        if liquidity_balance != 0:

            await self.client.check_for_approved(
                pool_address, SYNCSWAP_CONTRACTS[self.network]['router'], liquidity_balance)

            total_supply = await pool_contract.functions.totalSupply().call()
            _, reserve_eth = await pool_contract.functions.getReserves().call()
            min_eth_amount_out = int(liquidity_balance * reserve_eth / total_supply * 2 * 0.9965)

            withdraw_mode = 1
            data = abi.encode(['address', 'address', 'uint8'],
                              [token_a_address, self.client.address, withdraw_mode])

            tx_params = await self.client.prepare_transaction()
            transaction = await self.router_contract.functions.burnLiquiditySingle(
                pool_address,
                liquidity_balance,
                data,
                min_eth_amount_out,
                ZERO_ADDRESS,
                "0x",
            ).build_transaction(tx_params)

            return await self.client.verify_transaction(transaction)

        else:
            raise RuntimeError('Insufficient balance on SyncSwap!')
