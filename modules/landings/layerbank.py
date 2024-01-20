from config import LAYERBANK_CONTRACTS, LAYERBANK_ABI
from utils.tools import gas_checker, helper
from modules import Landing, Logger


class LayerBank(Landing, Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)

        self.network = self.client.network.name
        self.landing_contract = self.client.get_contract(LAYERBANK_CONTRACTS[self.network]['landing'], LAYERBANK_ABI)
        self.pool_contract = self.client.get_contract(LAYERBANK_CONTRACTS[self.network]['pool'])

    @helper
    @gas_checker
    async def deposit(self):

        amount, amount_in_wei = await self.client.check_and_get_eth()

        self.client.logger_msg(*self.client.acc_info, msg=f'Deposit to LayerBank: {amount} ETH')

        tx_params = await self.client.prepare_transaction(value=amount_in_wei)

        transaction = await self.landing_contract.functions.supply(
            LAYERBANK_CONTRACTS[self.network]['pool'],
            amount_in_wei
        ).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)

    @helper
    @gas_checker
    async def withdraw(self):
        liquidity_balance_in_wei = await self.pool_contract.functions.balanceOf(self.client.address).call()

        liquidity_balance = f"{liquidity_balance_in_wei / 10 ** 18:.4f}"

        self.client.logger_msg(*self.client.acc_info, msg=f'Withdraw {liquidity_balance} ETH from LayerBank')

        if liquidity_balance_in_wei != 0:

            tx_params = await self.client.prepare_transaction()

            transaction = await self.landing_contract.functions.redeemUnderlying(
                LAYERBANK_CONTRACTS[self.network]['pool'],
                liquidity_balance_in_wei,
            ).build_transaction(tx_params)

            return await self.client.send_transaction(transaction)
        else:
            raise RuntimeError("Insufficient balance on LayerBank!")

    @helper
    @gas_checker
    async def enable_collateral(self):
        self.client.logger_msg(*self.client.acc_info, msg=f'Enable collateral on LayerBank')

        tx_params = await self.client.prepare_transaction()

        transaction = await self.landing_contract.functions.enterMarkets(
            [LAYERBANK_CONTRACTS[self.network]['pool']]
        ).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)

    @helper
    @gas_checker
    async def disable_collateral(self):
        self.client.logger_msg(*self.client.acc_info, msg=f'Disable collateral on LayerBank')

        tx_params = await self.client.prepare_transaction()

        transaction = await self.landing_contract.functions.exitMarket(
            LAYERBANK_CONTRACTS[self.network]['pool']
        ).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)
