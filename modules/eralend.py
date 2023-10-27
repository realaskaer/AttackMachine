from config import ERALEND_CONTRACTS, ERALEND_ABI
from utils.tools import gas_checker, repeater
from modules import Client


class Eralend(Client):
    def __init__(self, account_number, private_key, network, proxy=None):
        super().__init__(account_number, private_key, network, proxy)
        self.landing_contract = self.get_contract(ERALEND_CONTRACTS['landing'], ERALEND_ABI)
        self.collateral_contract = self.get_contract(ERALEND_CONTRACTS['collateral'], ERALEND_ABI)

    @repeater
    @gas_checker
    async def deposit(self):

        amount, amount_in_wei = await self.check_and_get_eth_for_deposit()

        self.logger.info(f'{self.info} Deposit to EraLend: {amount} ETH')

        tx_params = (await self.prepare_transaction()) | {
            'to': ERALEND_CONTRACTS['landing'],
            'value': amount_in_wei,
            'data': '0x1249c58b'
        }

        tx_hash = await self.send_transaction(tx_params)

        await self.verify_transaction(tx_hash)

    @repeater
    @gas_checker
    async def withdraw(self):
        self.logger.info(f'{self.info} Withdraw from EraLend')

        liquidity_balance = await self.landing_contract.functions.balanceOfUnderlying(self.address).call()

        if liquidity_balance != 0:

            tx_params = await self.prepare_transaction()

            transaction = await self.landing_contract.functions.redeemUnderlying(
                liquidity_balance
            ).build_transaction(tx_params)

            tx_hash = await self.send_transaction(transaction)

            await self.verify_transaction(tx_hash)

        else:
            self.logger.error(f'{self.info} Insufficient balance on EraLend!')

    @repeater
    @gas_checker
    async def enable_collateral(self):
        self.logger.info(f'{self.info} Enable collateral on EraLend')

        tx_params = await self.prepare_transaction()

        transaction = await self.collateral_contract.functions.enterMarkets(
            [ERALEND_CONTRACTS['landing']]
        ).build_transaction(tx_params)

        tx_hash = await self.send_transaction(transaction)

        await self.verify_transaction(tx_hash)

    @repeater
    @gas_checker
    async def disable_collateral(self):
        self.logger.info(f'{self.info} Disable collateral on EraLend')

        tx_params = await self.prepare_transaction()

        transaction = await self.collateral_contract.functions.exitMarket(
            ERALEND_CONTRACTS['landing']
        ).build_transaction(tx_params)

        tx_hash = await self.send_transaction(transaction)

        await self.verify_transaction(tx_hash)
