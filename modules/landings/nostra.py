from utils.tools import gas_checker, helper
from modules import Landing, Logger
from config import NOSTRA_CONTRACTS


class Nostra(Landing, Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)

    @helper
    @gas_checker
    async def deposit(self):
        await self.client.initialize_account()

        token_name, token_address, amount, amount_in_wei = await self.client.get_landing_data('Nostra', True)

        nostra_contract_address = NOSTRA_CONTRACTS[token_name]

        self.logger_msg(*self.client.acc_info, msg=f'Deposit to Nostra: {amount} {token_name}')

        approve_call = self.client.get_approve_call(token_address, nostra_contract_address, amount_in_wei)

        nostra_token_contract = await self.client.get_contract(contract_address=nostra_contract_address)

        deposit_call = nostra_token_contract.functions["mint"].prepare(
            self.client.address,
            amount_in_wei
        )

        return await self.client.send_transaction(approve_call, deposit_call)

    @helper
    @gas_checker
    async def withdraw(self):
        await self.client.initialize_account()

        token_name, _, landing_balance = await self.client.get_landing_data('Nostra')

        amount = await self.client.get_normalize_amount(landing_balance)

        self.logger_msg(*self.client.acc_info, msg=f'Withdraw {amount:.4f} {token_name} from Nostra')

        nostra_contract = await self.client.get_contract(NOSTRA_CONTRACTS[token_name])

        withdraw_call = nostra_contract.functions["burn"].prepare(
            self.client.address,
            self.client.address,
            landing_balance
        )

        return await self.client.send_transaction(withdraw_call)

    async def enable_collateral(self):
        pass

    async def disable_collateral(self):
        pass
