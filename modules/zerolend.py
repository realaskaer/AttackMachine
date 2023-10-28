from utils.tools import gas_checker, repeater
from config import ZEROLEND_CONTRACTS, ZEROLEND_ABI, ZKSYNC_TOKENS
from modules import Client


class ZeroLend(Client):
    def __init__(self, account_number, private_key, network, proxy=None):
        super().__init__(account_number, private_key, network, proxy)
        self.landing_contract = self.get_contract(ZEROLEND_CONTRACTS['landing'], ZEROLEND_ABI)
        self.collateral_contract = self.get_contract(ZEROLEND_CONTRACTS['pool_proxy'], ZEROLEND_ABI)

    @repeater
    @gas_checker
    async def deposit(self):

        amount, amount_in_wei = await self.check_and_get_eth_for_deposit()

        self.logger.info(f'{self.info} Deposit to ZeroLend: {amount} ETH')

        tx_params = await self.prepare_transaction(value=amount_in_wei)

        transaction = await self.landing_contract.functions.depositETH(
            ZEROLEND_CONTRACTS['pool_proxy'],
            self.address,
            0
        ).build_transaction(tx_params)

        tx_hash = await self.send_transaction(transaction)

        await self.verify_transaction(tx_hash)

    @repeater
    @gas_checker
    async def withdraw(self):
        self.logger.info(f'{self.info} Withdraw liquidity from ZeroLend')

        liquidity_balance = await self.get_contract(ZEROLEND_CONTRACTS['weth_atoken']).functions.balanceOf(
            self.address).call()

        if liquidity_balance != 0:

            await self.check_for_approved(ZEROLEND_CONTRACTS['weth_atoken'], ZEROLEND_CONTRACTS['landing'],
                                          liquidity_balance)

            tx_params = await self.prepare_transaction()

            transaction = await self.landing_contract.functions.withdrawETH(
                ZEROLEND_CONTRACTS['pool_proxy'],
                liquidity_balance,
                self.address
            ).build_transaction(tx_params)

            tx_hash = await self.send_transaction(transaction)

            await self.verify_transaction(tx_hash)

        else:
            raise RuntimeError('Insufficient balance on ZeroLend!')

    @repeater
    @gas_checker
    async def enable_collateral(self):
        self.logger.info(f'{self.info} Enable collateral on ZeroLend')

        tx_params = await self.prepare_transaction()

        transaction = await self.collateral_contract.functions.setUserUseReserveAsCollateral(
            ZKSYNC_TOKENS['ETH'],
            True
        ).build_transaction(tx_params)

        tx_hash = await self.send_transaction(transaction)

        await self.verify_transaction(tx_hash)

    @repeater
    @gas_checker
    async def disable_collateral(self):
        self.logger.info(f'{self.info} Disable collateral on ZeroLend')

        tx_params = await self.prepare_transaction()

        transaction = await self.collateral_contract.functions.setUserUseReserveAsCollateral(
            ZKSYNC_TOKENS['ETH'],
            False
        ).build_transaction(tx_params)

        tx_hash = await self.send_transaction(transaction)

        await self.verify_transaction(tx_hash)
