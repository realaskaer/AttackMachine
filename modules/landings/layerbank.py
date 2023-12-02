from config import LAYERBANK_CONTRACTS, LAYERBANK_ABI
from utils.tools import gas_checker, repeater
from modules import Landing


class LayerBank(Landing):
    def __init__(self, client):
        self.client = client

        self.network = self.client.network.name
        self.landing_contract = self.client.get_contract(LAYERBANK_CONTRACTS[self.network]['landing'], LAYERBANK_ABI)

    @repeater
    @gas_checker
    async def deposit(self):

        amount, amount_in_wei = await self.client.check_and_get_eth_for_deposit()

        self.client.logger.info(f'{self.client.info} LayerBank | Deposit to LayerBank: {amount} ETH')

        tx_params = await self.client.prepare_transaction(value=amount_in_wei)

        transaction = await self.landing_contract.functions.supply(
            LAYERBANK_CONTRACTS['pool'],
            amount_in_wei
        ).build_transaction(tx_params)

        tx_hash = await self.client.send_transaction(transaction)

        await self.client.verify_transaction(tx_hash)

    @repeater
    @gas_checker
    async def withdraw(self):
        liquidity_balance_in_wei = await self.landing_contract.functions.balanceOf(self.client.address).call()

        liquidity_balance = f"{liquidity_balance_in_wei / 10 ** 18:.4f}"

        self.client.logger.info(f'{self.client.info} LayerBank | Withdraw {liquidity_balance} ETH from LayerBank')

        if liquidity_balance_in_wei != 0:

            tx_params = await self.client.prepare_transaction()

            transaction = await self.landing_contract.functions.redeemUnderlying(
                LAYERBANK_CONTRACTS['pool'],
                liquidity_balance_in_wei,
            ).build_transaction(tx_params)

            tx_hash = await self.client.send_transaction(transaction)

            await self.client.verify_transaction(tx_hash)
        else:
            raise RuntimeError("Insufficient balance on LayerBank!")

    @repeater
    @gas_checker
    async def enable_collateral(self):
        self.client.logger.info(f'{self.client.info} LayerBank | Enable collateral on LayerBank')

        tx_params = await self.client.prepare_transaction()

        transaction = await self.landing_contract.functions.enterMarkets(
            [LAYERBANK_CONTRACTS['pool']]
        ).build_transaction(tx_params)

        tx_hash = await self.client.send_transaction(transaction)

        await self.client.verify_transaction(tx_hash)

    @repeater
    @gas_checker
    async def disable_collateral(self):
        self.client.logger.info(f'{self.client.info} LayerBank | Disable collateral on LayerBank')

        tx_params = await self.client.prepare_transaction()

        transaction = await self.landing_contract.functions.exitMarket(
            LAYERBANK_CONTRACTS['pool']
        ).build_transaction(tx_params)

        tx_hash = await self.client.send_transaction(transaction)

        await self.client.verify_transaction(tx_hash)
