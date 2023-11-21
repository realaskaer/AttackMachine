from settings import USE_PROXY
from utils.tools import gas_checker, repeater
from modules import Landing
from config import CARMINE_CONTRACT, TOKENS_PER_CHAIN


class Carmine(Landing):
    def __init__(self, client):
        self.client = client

    async def check_landing_balance(self, contract_address:str):

        pool_address = (await self.client.account.client.call_contract(self.client.prepare_call(
            contract_address=contract_address,
            selector_name="get_lptoken_address_for_given_option",
            calldata=[
                TOKENS_PER_CHAIN[self.client.network.name]['USDC'],
                TOKENS_PER_CHAIN[self.client.network.name]['ETH'],
                0
            ]
        )))[0]

        landing_balance = (await self.client.account.client.call_contract(self.client.prepare_call(
            contract_address=contract_address,
            selector_name="get_user_pool_infos",
            calldata=[pool_address]  # TODO непоняток блять, откуда брать инфу о балансе
        ))).balance
        print(landing_balance)
        if landing_balance > 0:
            return landing_balance, landing_balance * 10 ** 18

        raise RuntimeError('Insufficient balance on zkLend!')

    @repeater
    @gas_checker
    async def deposit(self):
        try:
            await self.client.initialize_account()

            amount, amount_in_wei = await self.client.check_and_get_eth_for_deposit()

            self.client.logger.info(f'{self.client.info} Deposit to Carmine: {amount} ETH to ETH/USDC pool')

            landing_contract = CARMINE_CONTRACT['landing']

            approve_call = self.client.get_approve_call(TOKENS_PER_CHAIN[self.client.network.name]['ETH'],
                                                        landing_contract, amount_in_wei)

            deposit_call = self.client.prepare_call(
                contract_address=landing_contract,
                selector_name="deposit_liquidity",
                calldata=[
                    TOKENS_PER_CHAIN[self.client.network.name]['ETH'],
                    TOKENS_PER_CHAIN[self.client.network.name]['USDC'],
                    TOKENS_PER_CHAIN[self.client.network.name]['ETH'],
                    0,
                    amount_in_wei, 0
                ]
            )

            return await self.client.send_transaction(approve_call, deposit_call)
        finally:
            if USE_PROXY:
                await self.client.session.close()

    @repeater
    @gas_checker
    async def withdraw(self):
        try:
            await self.client.initialize_account()

            landing_contract = CARMINE_CONTRACT['landing']

            landing_balance, landing_balance_in_wei = await self.check_landing_balance(landing_contract)

            self.client.logger.info(f'{self.client.info} Withdraw {landing_balance} ETH from Carmine ETH/USDC Pool')

            withdraw_call = self.client.prepare_call(
                contract_address=landing_contract,
                selector_name="withdraw_liquidity",
                calldata=[
                    TOKENS_PER_CHAIN[self.client.network.name]['ETH'],
                    TOKENS_PER_CHAIN[self.client.network.name]['USDC'],
                    TOKENS_PER_CHAIN[self.client.network.name]['ETH'],
                    0,
                    landing_balance_in_wei, 0
                ]
            )
            print(withdraw_call)
            return
            return await self.client.send_transaction(withdraw_call)
        finally:
            if USE_PROXY:
                await self.client.session.close()

    async def enable_collateral(self):
        pass

    async def disable_collateral(self):
        pass
