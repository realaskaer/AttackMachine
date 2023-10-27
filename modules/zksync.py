import random
# from web3._utils.contracts import encode_abi
# from web3._utils.abi import get_constructor_abi, merge_args_and_kwargs
# from hashlib import sha256
from eth_account import Account
from modules import Client
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


class ZkSync(Client):
    def __init__(self, account_number, private_key, network, proxy=None):
        super().__init__(account_number, private_key, network, proxy)
        self.deposit_contract = self.get_contract(ZKSYNC_CONTRACTS['deposit'], ZKSYNC_DEPOSIT_ABI)
        self.withdraw_contract = self.get_contract(ZKSYNC_CONTRACTS['withdraw'], ZKSYNC_WITHDRAW_ABI)
        self.token_contract = self.get_contract(ZKSYNC_TOKENS['WETH'], WETH_ABI)
        # self.deployer_contract = self.get_contract(ZKSYNC_CONTRACTS['contact_delpoyer'], CONTRACT_DEPLOYER_ABI)

    @repeater
    @gas_checker
    async def deposit(self):

        amount = self.round_amount(TXSYNC_DEP_MIN, TXSYNC_DEP_MAX)
        amount_in_wei = int(amount * 10 ** 18)

        self.logger.info(f'{self.info} Bridge on txSync: {amount} ETH ERC20 -> zkSync Era')

        if await self.w3.eth.get_balance(self.address) > amount_in_wei:

            gas_limit = random.randint(750000, 1000000)

            base_cost_in_wei = await self.deposit_contract.functions.l2TransactionBaseCost(
                self.w3.eth.gas_price,
                gas_limit,
                800
            ).call()

            tx_params = await self.prepare_transaction(value=amount_in_wei + base_cost_in_wei)

            transaction = await self.deposit_contract.functions.requestL2Transaction(
                self.address,
                amount_in_wei,
                "0x",
                gas_limit,
                800,
                [],
                self.address
            ).build_transaction(tx_params)

            tx_hash = await self.send_transaction(transaction)

            await self.verify_transaction(tx_hash)

        else:
            self.logger.error(f'{self.info} Bridge on txSync | Insufficient balance!')

    @repeater
    @gas_checker
    async def withdraw(self):

        amount = self.round_amount(TXSYNC_WITHDRAW_MIN, TXSYNC_WITHDRAW_MAX)
        amount_in_wei = int(amount * 10 ** 18)

        self.logger.info(f'{self.info} Withdraw on txSync: {amount} ETH zkSync Era -> ERC20')

        if await self.w3.eth.get_balance(self.address) > amount_in_wei:

            tx_params = await self.prepare_transaction(value=amount_in_wei)

            transaction = await self.withdraw_contract.functions.withdraw(
                self.address,
            ).build_transaction(tx_params)

            tx_hash = await self.send_transaction(transaction)

            await self.verify_transaction(tx_hash)

        else:
            self.logger.error(f'{self.info} Withdraw on txSync | Insufficient balance!')

    @repeater
    @gas_checker
    async def transfer_eth(self):

        amount = self.round_amount(TRANSFER_MIN, TRANSFER_MAX)
        amount_in_wei = int(amount * 10 ** 18)
        random_address = Account.create().address

        self.logger.info(f'{self.info}| Transfer ETH to random zkSync address: {amount} ETH')

        if await self.w3.eth.get_balance(self.address) > amount_in_wei:

            tx_params = (await self.prepare_transaction()) | {
                'to': random_address,
                'value': amount_in_wei,
                'data': "0x"
            }

            tx_hash = await self.send_transaction(tx_params)

            await self.verify_transaction(tx_hash)

        else:
            self.logger.error(f'{self.info} Insufficient balance!')

    # @repeater
    # @gas_checker
    # async def transfer_erc20_tokens(self, token_to_sent_name: str, address_to_sent: str, amount: float):
    #
    #     self.logger.info(f'{self.info} Transfer {token_to_sent_name} to random address: {amount} {token_to_sent_name}')
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

        amount, amount_in_wei = await self.check_and_get_eth_for_deposit()

        self.logger.info(f'{self.info} Wrap {amount} ETH')

        if await self.w3.eth.get_balance(self.address) > amount_in_wei:

            tx_params = await self.prepare_transaction(value=amount_in_wei)
            transaction = await self.token_contract.functions.deposit().build_transaction(tx_params)

            tx_hash = await self.send_transaction(transaction)

            await self.verify_transaction(tx_hash)

        else:
            self.logger.error(f'{self.info} Insufficient balance!')

    @repeater
    @gas_checker
    async def unwrap_eth(self):

        amount, amount_in_wei = await self.get_token_balance('WETH', check_symbol=False)

        self.logger.info(f'{self.info} Unwrap {amount} WETH')

        tx_params = await self.prepare_transaction()

        transaction = await self.token_contract.functions.withdraw(
            amount_in_wei
        ).build_transaction(tx_params)

        tx_hash = await self.send_transaction(transaction)

        await self.verify_transaction(tx_hash)


    # def deploy_contract(self, token_name: str, token_symbol: str):
    #
    #     self.logger.info(f"{self.info} Contract deployment initiated")
    #
    #     constructor_args = {
    #         '_defaultAdmin': '0x56Abb6a3f25DCcdaDa106191053b1CC54C196DEE',
    #         '_name': token_name,
    #         '_symbol': token_symbol,
    #         '_contractURI': 'ipfs://qmpbdhsebfdbxih1gtrbasne1qpupbpdyldn5stuktiteu/1',
    #         '_trustedForwarders': ['0x4e0C3577335961Ff800FFDA24981EB2F38D94483'],
    #         '_primarySaleRecipient': self.address,
    #         '_platformFeeRecipient': self.address,
    #         '_platformFeeBps': 1000
    #     }
    #     from config import TEST
    #     token_contract = self.w3.eth.contract(abi=TOKEN_DEPLOY_ABI['abi'], bytecode=TOKEN_DEPLOY_ABI['bytecode'])
    #
    #     constructor_abi = get_constructor_abi(TOKEN_DEPLOY_ABI['abi'])
    #     arguments = merge_args_and_kwargs(constructor_abi, (), constructor_args)
    #     encoded_constructor = encode_abi(self.w3, constructor_abi, arguments)
    #
    #     token_contract.constructor(**constructor_args).build_transaction()
    #
    #     def hash_byte_code(bytecode: bytes) -> bytes:
    #         bytecode_len = len(bytecode)
    #         bytecode_size = int(bytecode_len / 32)
    #         bytecode_hash = sha256(bytecode).digest()
    #         encoded_len = bytecode_size.to_bytes(2, byteorder='big')
    #         return b'\x01\00' + encoded_len + bytecode_hash[4:]
    #
    #     tx_params = self.prepare_transaction()
    #     print(encoded_constructor)
    #     transaction = self.deployer_contract.functions.create(
    #         b'\0' * 32,
    #         hash_byte_code(token_contract.bytecode),
    #         encoded_constructor
    #     ).build_transaction(tx_params)
    #
    #     tx_hash = self.send_transaction(transaction)
    #
    #     self.verify_transaction(tx_hash)
    #
    #     contract_address = self.w3.eth.get_transaction_receipt(tx_hash)['contractAddress']
    #
    #     contract_info = f'{self.network.explorer}address/{contract_address}'
    #     self.logger.info(f"{self.info} Contract successfully deployed: contract_info")
    #
    #     with open('data/delpoy_zksync/delpoyed_tokens_data.json', 'r', encoding='utf-8') as file:
    #         deployed_tokens_data = json.load(file)
    #         deployed_tokens_data[f'{self.address}'] = {
    #             'contract_address': contract_address,
    #             'token_name': token_name
    #         }
    #
    #     with open('data/delpoy_zksync/delpoyed_tokens_data.json', 'w', encoding='utf-8') as file:
    #         json.dump(deployed_tokens_data, file, indent=4)
    #
    # def mint_token(self, token_address: str, amount: float):
    #
    #     with open('data/delpoy_zksync/delpoyed_tokens_data.json', 'r', encoding='utf-8') as file:
    #         delpoyed_tokens_data = json.load(file)
    #         token_name = delpoyed_tokens_data[f'{self.address}']['token_name']
    #         token_contract = self.get_contract(
    #             delpoyed_tokens_data[f'{self.address}']['contract_address'],
    #             TOKEN_DEPLOY_ABI['abi']
    #         )
    #
    #     self.logger.info(f"{self.info} Mint token: {amount} {token_name} token minting initiated")
    #
    #     tx_params = self.prepare_transaction()
    #
    #     transaction = token_contract.functions.mintTo(
    #         self.address,
    #         amount * 10 ** 18
    #     ).build_transaction(tx_params)
    #
    #     tx_hash = self.send_transaction(transaction)
    #
    #     self.verify_transaction(tx_hash)
