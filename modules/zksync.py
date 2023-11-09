import random

from eth_account import Account
from modules import Blockchain
from utils.tools import gas_checker, repeater
from settings import (
    TXSYNC_DEP_MAX,
    TXSYNC_DEP_MIN,
    TXSYNC_WITHDRAW_MAX,
    TXSYNC_WITHDRAW_MIN,
    TRANSFER_MIN,
    TRANSFER_MAX
)
from config import (
    WETH_ABI,
    ZKSYNC_TOKENS,
    ZKSYNC_CONTRACTS,
    ZKSYNC_DEPOSIT_ABI,
    ZKSYNC_WITHDRAW_ABI,
)


class ZkSync(Blockchain):
    def __init__(self, client):
        self.client = client

        self.deposit_contract = self.client.get_contract(ZKSYNC_CONTRACTS['deposit'], ZKSYNC_DEPOSIT_ABI)
        self.withdraw_contract = self.client.get_contract(ZKSYNC_CONTRACTS['withdraw'], ZKSYNC_WITHDRAW_ABI)
        self.token_contract = self.client.get_contract(ZKSYNC_TOKENS['WETH'], WETH_ABI)

    @repeater
    @gas_checker
    async def deposit(self):

        amount = self.client.round_amount(TXSYNC_DEP_MIN, TXSYNC_DEP_MAX)
        amount_in_wei = int(amount * 10 ** 18)

        self.client.logger.info(f'{self.client.info} zkSync | Bridge on txSync: {amount} ETH ERC20 -> zkSync Era')

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

            tx_hash = await self.client.send_transaction(transaction)

            await self.client.verify_transaction(tx_hash)

        else:
            raise RuntimeError('Bridge on txSync | Insufficient balance!')

    @repeater
    @gas_checker
    async def withdraw(self):

        amount = self.client.round_amount(TXSYNC_WITHDRAW_MIN, TXSYNC_WITHDRAW_MAX)
        amount_in_wei = int(amount * 10 ** 18)

        self.client.logger.info(f'{self.client.info} zkSync | Withdraw on txSync: {amount} ETH zkSync Era -> ERC20')

        if await self.client.w3.eth.get_balance(self.client.address) > amount_in_wei:

            tx_params = await self.client.prepare_transaction(value=amount_in_wei)

            transaction = await self.withdraw_contract.functions.withdraw(
                self.client.address,
            ).build_transaction(tx_params)

            tx_hash = await self.client.send_transaction(transaction)

            await self.client.verify_transaction(tx_hash)

        else:
            raise RuntimeError('Withdraw on txSync | Insufficient balance!')

    @repeater
    @gas_checker
    async def transfer_eth_to_myself(self):

        amount, amount_in_wei = self.client.check_and_get_eth_for_deposit()

        self.client.logger.info(
            f"{self.client.info} zkSync | Transfer {amount} ETH to your own address: {self.client.address}")

        tx_params = await self.client.prepare_transaction(value=amount_in_wei) | {
            "to": self.client.address,
            "data": "0x"
        }

        tx_hash = await self.client.send_transaction(tx_params)

        await self.client.verify_transaction(tx_hash)

    @repeater
    @gas_checker
    async def transfer_eth(self):

        amount = self.client.round_amount(TRANSFER_MIN, TRANSFER_MAX)
        amount_in_wei = int(amount * 10 ** 18)
        random_address = Account.create().address

        self.client.logger.info(f'{self.client.info} zkSync | Transfer ETH to random zkSync address: {amount} ETH')

        if await self.client.w3.eth.get_balance(self.client.address) > amount_in_wei:

            tx_params = (await self.client.prepare_transaction()) | {
                'to': random_address,
                'value': amount_in_wei,
                'data': "0x"
            }

            tx_hash = await self.client.send_transaction(tx_params)

            await self.client.verify_transaction(tx_hash)

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

        self.client.logger.info(f'{self.client.info} zkSync | Wrap {amount} ETH')

        if await self.client.w3.eth.get_balance(self.client.address) > amount_in_wei:

            tx_params = await self.client.prepare_transaction(value=amount_in_wei)
            transaction = await self.token_contract.functions.deposit().build_transaction(tx_params)

            tx_hash = await self.client.send_transaction(transaction)

            await self.client.verify_transaction(tx_hash)

        else:
            raise RuntimeError('Insufficient balance!')

    @repeater
    @gas_checker
    async def unwrap_eth(self):

        amount_in_wei, amount, _ = await self.client.get_token_balance('WETH', check_symbol=False)

        self.client.logger.info(f'{self.client.info} zkSync | Unwrap {amount:.6f} WETH')

        tx_params = await self.client.prepare_transaction()

        transaction = await self.token_contract.functions.withdraw(
            amount_in_wei
        ).build_transaction(tx_params)

        tx_hash = await self.client.send_transaction(transaction)

        await self.client.verify_transaction(tx_hash)
