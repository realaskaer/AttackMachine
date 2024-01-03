import random

from modules import Landing, Logger
from config import ROCKETSAM_ABI, ROCKETSAM_CONTRACTS
from utils.tools import gas_checker, helper


class RocketSam(Landing, Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)
        self.network = self.client.network.name

    async def get_pool(self, withdraw_mode:bool = False):
        for contract_address in ROCKETSAM_CONTRACTS[self.network]:
            contract = self.client.get_contract(contract_address, ROCKETSAM_ABI)
            contract_balance = await contract.functions.balances(self.client.address).call()
            if withdraw_mode:
                if contract_balance != 0:
                    return contract, contract_address, contract_balance
            else:
                if contract_balance == 0:
                    return contract, contract_address
        if withdraw_mode:
            raise RuntimeError('Insufficient balance on RocketSam!')
        else:
            self.logger_msg(
                *self.client.acc_info, msg=f'All pools have been used, take a random one', type_msg='warning')
            contract_address = random.choice(ROCKETSAM_CONTRACTS[self.network])
            return self.client.get_contract(contract_address, ROCKETSAM_ABI), contract_address

    @helper
    @gas_checker
    async def deposit(self):
        amount, amount_in_wei = await self.client.check_and_get_eth()

        pool_contract, pool_address = await self.get_pool()

        self.logger_msg(*self.client.acc_info, msg=f'Deposit {amount} ETH to RocketSam. Pool address: {pool_address}')

        fee = await pool_contract.functions.estimateProtocolFee(amount_in_wei).call()

        transaction = await pool_contract.functions.depositWithReferrer(
            "0x000000a679C2FB345dDEfbaE3c42beE92c0Fb7A5",
            amount_in_wei
        ).build_transaction(await self.client.prepare_transaction(value=amount_in_wei + fee))

        return await self.client.send_transaction(transaction)

    @helper
    @gas_checker
    async def withdraw(self):
        pool_contract, pool_address, pool_balance = await self.get_pool(withdraw_mode=True)

        transaction = await pool_contract.functions.withdraw().build_transaction(
            await self.client.prepare_transaction()
        )

        return await self.client.send_transaction(transaction)

    async def enable_collateral(self):
        pass

    async def disable_collateral(self):
        pass
