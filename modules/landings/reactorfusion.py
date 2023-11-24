from utils.tools import gas_checker, repeater
from config import REACTORFUSION_CONTRACTS, REACTORFUSION_ABI
from modules import Landing, Logger


class ReactorFusion(Landing, Logger):
    def __init__(self, client):
        super().__init__()
        self.client = client

        self.landing_contract = self.client.get_contract(REACTORFUSION_CONTRACTS['landing'], REACTORFUSION_ABI)
        self.collateral_contract = self.client.get_contract(REACTORFUSION_CONTRACTS['collateral'], REACTORFUSION_ABI)

    @repeater
    @gas_checker
    async def deposit(self):

        amount, amount_in_wei = await self.client.check_and_get_eth_for_deposit()

        self.logger_msg(*self.client.acc_info, msg=f'Deposit to ReactorFusion: {amount} ETH')

        tx_params = await (self.client.prepare_transaction()) | {
            'to': REACTORFUSION_CONTRACTS['landing'],
            'value': amount_in_wei,
            'data': '0x1249c58b'
        }

        return await self.client.send_transaction(tx_params)

    @repeater
    @gas_checker
    async def withdraw(self):
        self.logger_msg(*self.client.acc_info, msg=f'ReactorFusion | Withdraw from ReactorFusion')

        liquidity_balance = await self.landing_contract.functions.balanceOf(self.client.address).call()

        if liquidity_balance != 0:

            tx_params = await self.client.prepare_transaction()

            transaction = await self.landing_contract.functions.redeem(
                liquidity_balance
            ).build_transaction(tx_params)

            return await self.client.send_transaction(transaction)

        else:
            raise RuntimeError("Insufficient balance on ReactorFusion!")

    @repeater
    @gas_checker
    async def enable_collateral(self):
        self.logger_msg(*self.client.acc_info, msg=f'ReactorFusion | Enable collateral on ReactorFusion')

        tx_params = await self.client.prepare_transaction()

        transaction = await self.collateral_contract.functions.enterMarkets(
            [REACTORFUSION_CONTRACTS['landing']]
        ).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)

    @repeater
    @gas_checker
    async def disable_collateral(self):
        self.logger_msg(*self.client.acc_info, msg=f'ReactorFusion | Disable collateral on ReactorFusion')

        tx_params = await self.client.prepare_transaction()

        transaction = await self.collateral_contract.functions.exitMarket(
            REACTORFUSION_CONTRACTS['landing']
        ).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)
