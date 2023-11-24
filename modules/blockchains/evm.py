import random

from starknet_py.hash.selector import get_selector_from_name
from starknet_py.net.full_node_client import FullNodeClient


from eth_account import Account
from modules import Blockchain, Logger
from utils.networks import StarknetRPC
from utils.tools import gas_checker, repeater
from settings import (
    NATIVE_DEPOSIT_AMOUNT,
    NATIVE_WITHDRAW_AMOUNT,
    TRANSFER_AMOUNT
)
from config import (
    WETH_ABI,
    TOKENS_PER_CHAIN,
    NATIVE_CONTRACTS_PER_CHAIN,
    NATIVE_ABI,
)


class ZkSync(Blockchain, Logger):
    def __init__(self, client):
        Logger.__init__(self)
        super().__init__(client)

        self.deposit_contract = self.client.get_contract(NATIVE_CONTRACTS_PER_CHAIN['zkSync']['deposit'],
                                                         NATIVE_ABI['zkSync']['deposit'])
        self.withdraw_contract = self.client.get_contract(NATIVE_CONTRACTS_PER_CHAIN['zkSync']['withdraw'],
                                                          NATIVE_ABI['zkSync']['withdraw'])
        self.token_contract = self.client.get_contract(TOKENS_PER_CHAIN['zkSync']['WETH'],
                                                       WETH_ABI)

    @repeater
    @gas_checker
    async def deposit(self):

        amount = await self.client.get_smart_amount(NATIVE_DEPOSIT_AMOUNT)
        amount_in_wei = int(amount * 10 ** 18)

        self.logger_msg(*self.client.acc_info, msg=f'Bridge on txSync: {amount} ETH ERC20 -> zkSync Era')

        if await self.client.w3.eth.get_balance(self.client.address) > amount_in_wei:

            gas_limit = random.randint(750000, 1000000)

            base_cost_in_wei = await self.deposit_contract.functions.l2TransactionBaseCost(
                self.client.w3.eth.gas_price,
                gas_limit,
                800
            ).call()

            tx_params = await self.client.prepare_transaction(value=amount_in_wei + base_cost_in_wei)

            transaction = await self.deposit_contract.functions.requestL2Transaction(
                self.client.address,
                amount_in_wei,
                "0x",
                gas_limit,
                800,
                [],
                self.client.address
            ).build_transaction(tx_params)

            return await self.client.send_transaction(transaction)

        else:
            raise RuntimeError('Bridge on txSync | Insufficient balance!')

    @repeater
    @gas_checker
    async def withdraw(self):

        amount = await self.client.get_smart_amount(NATIVE_WITHDRAW_AMOUNT)
        amount_in_wei = int(amount * 10 ** 18)

        self.logger_msg(*self.client.acc_info, msg=f'Withdraw on txSync: {amount} ETH zkSync Era -> ERC20')

        if await self.client.w3.eth.get_balance(self.client.address) > amount_in_wei:

            tx_params = await self.client.prepare_transaction(value=amount_in_wei)

            transaction = await self.withdraw_contract.functions.withdraw(
                self.client.address,
            ).build_transaction(tx_params)

            return await self.client.send_transaction(transaction)

        else:
            raise RuntimeError('Withdraw on txSync | Insufficient balance!')

    @repeater
    @gas_checker
    async def deploy_contract(self):

        try:
            with open('data/services/contact_data.json') as file:
                from json import load
                contract_data = load(file)
        except:
            raise RuntimeError("Bad data in contract_json.json")

        self.logger_msg(*self.client.acc_info, msg=f"Deploy contract on {self.client.network.name}")

        tx_data = await self.client.prepare_transaction()

        contract = self.client.w3.eth.contract(abi=contract_data['abi'], bytecode=contract_data['bytecode'])

        transaction = await contract.constructor().build_transaction(tx_data)

        return await self.client.send_transaction(transaction)

    @repeater
    @gas_checker
    async def transfer_eth_to_myself(self):

        amount, amount_in_wei = await self.client.check_and_get_eth_for_deposit(TRANSFER_AMOUNT)

        self.logger_msg(*self.client.acc_info, msg=f"Transfer {amount} ETH to your own address: {self.client.address}")

        tx_params = await self.client.prepare_transaction(value=amount_in_wei) | {
            "to": self.client.address,
            "data": "0x"
        }

        return await self.client.send_transaction(tx_params)

    @repeater
    @gas_checker
    async def transfer_eth(self):

        amount, amount_in_wei = await self.client.check_and_get_eth_for_deposit(TRANSFER_AMOUNT)

        random_address = Account.create().address

        self.logger_msg(*self.client.acc_info, msg=f'Transfer ETH to random zkSync address: {amount} ETH')

        if await self.client.w3.eth.get_balance(self.client.address) > amount_in_wei:

            tx_params = (await self.client.prepare_transaction()) | {
                'to': random_address,
                'value': amount_in_wei,
                'data': "0x"
            }

            return await self.client.send_transaction(tx_params)

        else:
            raise RuntimeError('Insufficient balance!')

    # @repeater
    # @gas_checker
    # async def transfer_erc20_tokens(self, token_to_sent_name: str, address_to_sent: str, amount: float):
    #
    #     self.logger.info(
#                       f'{self.info} Transfer {token_to_sent_name} to random address: {amount} {token_to_sent_name}')
    #
    #     amount_in_wei = await self.get_amount_in_wei(token_to_sent_name, amount)
    #
    #     if (await self.get_token_balance(ZKSYNC_TOKENS[token_to_sent_name]))['balance_in_wei'] >= amount_in_wei:
    #
    #         token_contract = self.get_contract(ZKSYNC_TOKENS[token_to_sent_name], ERC20_ABI)
    #
    #         tx_params = await self.prepare_transaction()
    #
    #         transaction = await token_contract.functions.transfer(
    #             address_to_sent,
    #             amount
    #         ).build_transaction(tx_params)
    #
    #         tx_hash = await self.send_transaction(transaction)
    #
    #         await self.verify_transaction(tx_hash)
    #
    #     else:
    #         self.logger.error(f'{self.info} Insufficient balance!')

    @repeater
    @gas_checker
    async def wrap_eth(self):

        amount, amount_in_wei = await self.client.check_and_get_eth_for_deposit()

        self.logger_msg(*self.client.acc_info, msg=f'Wrap {amount} ETH')

        if await self.client.w3.eth.get_balance(self.client.address) > amount_in_wei:

            tx_params = await self.client.prepare_transaction(value=amount_in_wei)
            transaction = await self.token_contract.functions.deposit().build_transaction(tx_params)

            return await self.client.send_transaction(transaction)

        else:
            raise RuntimeError('Insufficient balance!')

    @repeater
    @gas_checker
    async def unwrap_eth(self):

        amount_in_wei, amount, _ = await self.client.get_token_balance('WETH', check_symbol=False)

        self.logger_msg(*self.client.acc_info, msg=f'Unwrap {amount:.6f} WETH')

        tx_params = await self.client.prepare_transaction()

        transaction = await self.token_contract.functions.withdraw(
            amount_in_wei
        ).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)


class StarknetEVM(Blockchain, Logger):
    def __init__(self, client):
        Logger.__init__(self)
        super().__init__(client)

        self.evm_contract = self.client.get_contract(NATIVE_CONTRACTS_PER_CHAIN['Starknet']['evm_contract'],
                                                     NATIVE_ABI['Starknet'])

    async def get_starknet_deposit_fee(self, amount_in_wei: int):
        stark_w3 = FullNodeClient(random.choice(StarknetRPC.rpc))
        return (await stark_w3.estimate_message_fee(
            from_address=NATIVE_CONTRACTS_PER_CHAIN['Starknet']['evm_contract'],
            to_address=f"{NATIVE_CONTRACTS_PER_CHAIN['Starknet']['stark_contact']}",
            entry_point_selector=get_selector_from_name("handle_deposit"),
            payload=[
                self.client.address,
                amount_in_wei,
                0
            ]
        )).overall_fee

    @repeater
    @gas_checker
    async def deposit(self, receiver):

        amount = await self.client.get_smart_amount(NATIVE_DEPOSIT_AMOUNT)
        amount_in_wei = int(amount * 10 ** 18)

        self.logger_msg(*self.client.acc_info, msg=f'Bridge on StarkGate to {receiver}: {amount} ETH ERC20 -> Starknet')

        deposit_fee = await self.get_starknet_deposit_fee(amount_in_wei)

        tx_params = await self.client.prepare_transaction(value=amount_in_wei + deposit_fee)

        transaction = await self.evm_contract.functions.deposit(
            amount_in_wei,
            int(receiver, 16)
        ).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)
