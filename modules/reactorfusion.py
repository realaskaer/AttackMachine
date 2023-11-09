from utils.tools import gas_checker, repeater
from config import REACTORFUSION_CONTRACTS, REACTORFUSION_ABI
from modules import Landing


class ReactorFusion(Landing):
    def __init__(self, client):
        self.client = client

        self.landing_contract = self.client.get_contract(REACTORFUSION_CONTRACTS['landing'], REACTORFUSION_ABI)
        self.collateral_contract = self.client.get_contract(REACTORFUSION_CONTRACTS['collateral'], REACTORFUSION_ABI)

    @repeater
    @gas_checker
    async def deposit(self):

        amount, amount_in_wei = await self.client.check_and_get_eth_for_deposit()

        self.client.logger.info(f'{self.client.info} ReactorFusion | Deposit to ReactorFusion: {amount} ETH')

        tx_params = await (self.client.prepare_transaction()) | {
            'to': REACTORFUSION_CONTRACTS['landing'],
            'value': amount_in_wei,
            'data': '0x1249c58b'
        }

        tx_hash = await self.client.send_transaction(tx_params)

        await self.client.verify_transaction(tx_hash)

    @repeater
    @gas_checker
    async def withdraw(self):
        self.client.logger.info(f'{self.client.info} ReactorFusion | Withdraw from ReactorFusion')

        liquidity_balance = await self.landing_contract.functions.balanceOf(self.client.address).call()

        if liquidity_balance != 0:

            tx_params = await self.client.prepare_transaction()

            transaction = await self.landing_contract.functions.redeem(
                liquidity_balance
            ).build_transaction(tx_params)

            tx_hash = await self.client.send_transaction(transaction)

            await self.client.verify_transaction(tx_hash)

        else:
            raise RuntimeError("Insufficient balance on ReactorFusion!")

    @repeater
    @gas_checker
    async def enable_collateral(self):
        self.client.logger.info(f'{self.client.info} ReactorFusion | Enable collateral on ReactorFusion')

        tx_params = await self.client.prepare_transaction()

        transaction = await self.collateral_contract.functions.enterMarkets(
            [REACTORFUSION_CONTRACTS['landing']]
        ).build_transaction(tx_params)

        tx_hash = await self.client.send_transaction(transaction)

        await self.client.verify_transaction(tx_hash)

    @repeater
    @gas_checker
    async def disable_collateral(self):
        self.client.logger.info(f'{self.client.info} ReactorFusion | Disable collateral on ReactorFusion')

        tx_params = await self.client.prepare_transaction()

        transaction = await self.collateral_contract.functions.exitMarket(
            REACTORFUSION_CONTRACTS['landing']
        ).build_transaction(tx_params)

        tx_hash = await self.client.send_transaction(transaction)

        await self.client.verify_transaction(tx_hash)
