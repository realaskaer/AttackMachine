from config import MOONWELL_CONTRACTS, MOONWELL_ABI
from modules.interfaces import SoftwareException
from utils.tools import gas_checker, helper
from modules import Landing, Logger


class Moonwell(Landing, Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)

        self.network = self.client.network.name
        self.landing_contract = self.client.get_contract(
            MOONWELL_CONTRACTS[self.network]['landing'], MOONWELL_ABI['landing']
        )
        self.pool_contract = self.client.get_contract(
            MOONWELL_CONTRACTS[self.network]['weth_pool'], MOONWELL_ABI['weth_pool']
        )
        self.market_contract = self.client.get_contract(
            MOONWELL_CONTRACTS[self.network]['market'], MOONWELL_ABI['market']
        )

    @helper
    @gas_checker
    async def deposit(self):

        amount, amount_in_wei = await self.client.check_and_get_eth()

        self.client.logger_msg(*self.client.acc_info, msg=f'Deposit to Moonwell: {amount} ETH')

        tx_params = await self.client.prepare_transaction(value=amount_in_wei)

        transaction = await self.landing_contract.functions.mint(
            self.client.address
        ).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)

    @helper
    @gas_checker
    async def withdraw(self):
        liquidity_balance_in_wei = await self.pool_contract.functions.balanceOf(self.client.address).call()

        liquidity_balance = f"{liquidity_balance_in_wei / 10 ** 18:.4f}"

        self.client.logger_msg(*self.client.acc_info, msg=f'Withdraw {liquidity_balance} mWETH from Moonwell')

        if liquidity_balance_in_wei != 0:

            tx_params = await self.client.prepare_transaction()

            transaction = await self.pool_contract.functions.redeem(
                liquidity_balance_in_wei,
            ).build_transaction(tx_params)

            return await self.client.send_transaction(transaction)
        else:
            raise SoftwareException("Insufficient balance on Moonwell!")

    @helper
    @gas_checker
    async def enable_collateral(self):
        self.client.logger_msg(*self.client.acc_info, msg=f'Enable collateral on Moonwell')

        tx_params = await self.client.prepare_transaction()

        transaction = await self.market_contract.functions.enterMarkets(
            [self.pool_contract.address]
        ).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)

    @helper
    @gas_checker
    async def disable_collateral(self):
        self.client.logger_msg(*self.client.acc_info, msg=f'Disable collateral on Moonwell')

        tx_params = await self.client.prepare_transaction()

        transaction = await self.market_contract.functions.exitMarket(
            self.pool_contract.address
        ).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)
