from config import ABRACADABRA_CONTRACTS, ABRACADABRA_ABI, TOKENS_PER_CHAIN
from general_settings import LIQUIDITY_AMOUNT
from modules.interfaces import SoftwareException
from utils.tools import gas_checker, helper
from modules import Landing, Logger


class Abracadabra(Landing, Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)
        self.usdb_address = TOKENS_PER_CHAIN[self.client.network.name]['USDB']
        self.landing_contract = self.client.get_contract(
            ABRACADABRA_CONTRACTS[self.client.network.name]['landing'], ABRACADABRA_ABI
        )

    @helper
    @gas_checker
    async def deposit(self, lock:bool = False):

        amount = await self.client.get_smart_amount(LIQUIDITY_AMOUNT, token_name='USDB')
        amount_in_wei = self.client.to_wei(amount, 18)

        self.logger_msg(*self.client.acc_info, msg=f'Deposit to Abracadabra: {amount} USDB')

        await self.client.check_for_approved(self.usdb_address, self.landing_contract.address, amount_in_wei)

        transaction = await self.landing_contract.functions.deposit(
            self.usdb_address,
            amount_in_wei,
            True if lock else False
        ).build_transaction(await self.client.prepare_transaction())

        return await self.client.send_transaction(transaction)

    @helper
    @gas_checker
    async def withdraw(self):
        liquidity_balance, _, _ = await self.landing_contract.functions.balances(
            self.client.address, self.usdb_address
        ).call()

        self.logger_msg(*self.client.acc_info, msg=f'Withdraw {liquidity_balance / 10 ** 18:.2f} USDB from Abracadabra')

        if liquidity_balance != 0:

            tx_params = await self.client.prepare_transaction()

            transaction = await self.landing_contract.functions.withdraw(
                self.usdb_address,
                liquidity_balance
            ).build_transaction(tx_params)

            return await self.client.send_transaction(transaction)
        else:
            raise SoftwareException("Insufficient balance on Abracadabra!")
