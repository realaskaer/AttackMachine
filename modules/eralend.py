from config import ERALEND_CONTRACTS, ERALEND_ABI
from utils.tools import gas_checker, repeater
from modules import Landing


class EraLend(Landing):
    def __init__(self, client):
        self.client = client

        self.landing_contract = self.client.get_contract(ERALEND_CONTRACTS['landing'], ERALEND_ABI)
        self.collateral_contract = self.client.get_contract(ERALEND_CONTRACTS['collateral'], ERALEND_ABI)

    @repeater
    @gas_checker
    async def deposit(self):

        amount, amount_in_wei = await self.client.check_and_get_eth_for_deposit()

        self.client.logger.info(f'{self.client.info} EraLend | Deposit to EraLend: {amount} ETH')

        tx_params = (await self.client.prepare_transaction()) | {
            'to': ERALEND_CONTRACTS['landing'],
            'value': amount_in_wei,
            'data': '0x1249c58b'
        }

        tx_hash = await self.client.send_transaction(tx_params)

        await self.client.verify_transaction(tx_hash)

    @repeater
    @gas_checker
    async def withdraw(self):
        self.client.logger.info(f'{self.client.info} EraLend | Withdraw from EraLend')

        liquidity_balance = await self.landing_contract.functions.balanceOfUnderlying(self.client.address).call()

        if liquidity_balance != 0:

            tx_params = await self.client.prepare_transaction()

            transaction = await self.landing_contract.functions.redeemUnderlying(
                liquidity_balance
            ).build_transaction(tx_params)

            tx_hash = await self.client.send_transaction(transaction)

            await self.client.verify_transaction(tx_hash)

        else:
            raise RuntimeError(f'Insufficient balance on EraLend!')

    @repeater
    @gas_checker
    async def enable_collateral(self):
        self.client.logger.info(f'{self.client.info} EraLend | Enable collateral on EraLend')

        tx_params = await self.client.prepare_transaction()

        transaction = await self.collateral_contract.functions.enterMarkets(
            [ERALEND_CONTRACTS['landing']]
        ).build_transaction(tx_params)

        tx_hash = await self.client.send_transaction(transaction)

        await self.client.verify_transaction(tx_hash)

    @repeater
    @gas_checker
    async def disable_collateral(self):
        self.client.logger.info(f'{self.client.info} EraLend | Disable collateral on EraLend')

        tx_params = await self.client.prepare_transaction()

        transaction = await self.collateral_contract.functions.exitMarket(
            ERALEND_CONTRACTS['landing']
        ).build_transaction(tx_params)

        tx_hash = await self.client.send_transaction(transaction)

        await self.client.verify_transaction(tx_hash)
