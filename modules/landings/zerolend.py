from utils.tools import gas_checker, helper
from config import ZEROLEND_CONTRACTS, ZEROLEND_ABI, TOKENS_PER_CHAIN
from modules import Landing, Logger


class ZeroLend(Landing, Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)

        self.landing_contract = self.client.get_contract(ZEROLEND_CONTRACTS['landing'], ZEROLEND_ABI)
        self.collateral_contract = self.client.get_contract(ZEROLEND_CONTRACTS['pool_proxy'], ZEROLEND_ABI)

    @helper
    @gas_checker
    async def deposit(self):
        amount, amount_in_wei = await self.client.check_and_get_eth()

        self.logger_msg(*self.client.acc_info, msg=f'Deposit to ZeroLend: {amount} ETH')

        tx_params = await self.client.prepare_transaction(value=amount_in_wei)

        transaction = await self.landing_contract.functions.depositETH(
            ZEROLEND_CONTRACTS['pool_proxy'],
            self.client.address,
            0
        ).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)

    @helper
    @gas_checker
    async def withdraw(self):
        self.logger_msg(*self.client.acc_info, msg=f'Withdraw liquidity from ZeroLend')

        liquidity_balance = await self.client.get_contract(ZEROLEND_CONTRACTS['weth_atoken']).functions.balanceOf(
            self.client.address).call()

        if liquidity_balance != 0:

            await self.client.check_for_approved(ZEROLEND_CONTRACTS['weth_atoken'], ZEROLEND_CONTRACTS['landing'],
                                                 liquidity_balance)

            tx_params = await self.client.prepare_transaction()

            transaction = await self.landing_contract.functions.withdrawETH(
                ZEROLEND_CONTRACTS['pool_proxy'],
                liquidity_balance,
                self.client.address
            ).build_transaction(tx_params)

            return await self.client.send_transaction(transaction)

        else:
            raise RuntimeError('Insufficient balance on ZeroLend!')

    @helper
    @gas_checker
    async def enable_collateral(self):
        self.logger_msg(*self.client.acc_info, msg=f'Enable collateral on ZeroLend')

        tx_params = await self.client.prepare_transaction()

        transaction = await self.collateral_contract.functions.setUserUseReserveAsCollateral(
            TOKENS_PER_CHAIN[self.client.network.name]['ETH'],
            True
        ).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)

    @helper
    @gas_checker
    async def disable_collateral(self):
        self.logger_msg(*self.client.acc_info, msg=f'Disable collateral on ZeroLend')

        tx_params = await self.client.prepare_transaction()

        transaction = await self.collateral_contract.functions.setUserUseReserveAsCollateral(
            TOKENS_PER_CHAIN[self.client.network.name]['ETH'],
            False
        ).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)
