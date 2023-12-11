import random

from starknet_py.hash.selector import get_selector_from_name
from starknet_py.net.full_node_client import FullNodeClient


from eth_account import Account
from modules import Blockchain, Logger, Bridge
from utils.networks import StarknetRPC
from utils.tools import gas_checker, helper
from settings import (
    NATIVE_WITHDRAW_AMOUNT,
    NATIVE_DEPOSIT_AMOUNT,
    TRANSFER_AMOUNT
)
from config import (
    WETH_ABI,
    TOKENS_PER_CHAIN,
    NATIVE_CONTRACTS_PER_CHAIN,
    NATIVE_ABI,
)


class SimpleEVM(Logger):
    def __init__(self, client):
        Logger.__init__(self)
        self.client = client

        self.network = self.client.network.name
        self.deposit_contract = self.client.get_contract(
            NATIVE_CONTRACTS_PER_CHAIN[self.network]['deposit'],
            NATIVE_ABI[self.network]['deposit'])
        self.withdraw_contract = self.client.get_contract(
            NATIVE_CONTRACTS_PER_CHAIN[self.network]['withdraw'],
            NATIVE_ABI[self.network]['withdraw'])
        self.token_contract = self.client.get_contract(
            TOKENS_PER_CHAIN[self.client.network.name]['WETH'], WETH_ABI)

    @helper
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

    @helper
    @gas_checker
    async def transfer_eth_to_myself(self):

        amount, amount_in_wei = await self.client.check_and_get_eth(TRANSFER_AMOUNT)

        self.logger_msg(*self.client.acc_info, msg=f"Transfer {amount} ETH to your own address: {self.client.address}")

        tx_params = await self.client.prepare_transaction(value=amount_in_wei) | {
            "to": self.client.address,
            "data": "0x"
        }

        return await self.client.send_transaction(tx_params)

    @helper
    @gas_checker
    async def transfer_eth(self):

        amount, amount_in_wei = await self.client.check_and_get_eth(TRANSFER_AMOUNT)

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

    @helper
    @gas_checker
    async def wrap_eth(self):

        amount, amount_in_wei = await self.client.check_and_get_eth()

        self.logger_msg(*self.client.acc_info, msg=f'Wrap {amount} ETH')

        if await self.client.w3.eth.get_balance(self.client.address) > amount_in_wei:

            tx_params = await self.client.prepare_transaction(value=amount_in_wei)
            transaction = await self.token_contract.functions.deposit().build_transaction(tx_params)

            return await self.client.send_transaction(transaction)

        else:
            raise RuntimeError('Insufficient balance!')

    @helper
    @gas_checker
    async def unwrap_eth(self):

        amount_in_wei, amount, _ = await self.client.get_token_balance('WETH', check_symbol=False)

        self.logger_msg(*self.client.acc_info, msg=f'Unwrap {amount:.6f} WETH')

        tx_params = await self.client.prepare_transaction()

        transaction = await self.token_contract.functions.withdraw(
            amount_in_wei
        ).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)

    @helper
    @gas_checker
    async def random_approve(self):
        from config import (IZUMI_CONTRACTS, MAVERICK_CONTRACTS, MUTE_CONTRACTS, ODOS_CONTRACT, ONEINCH_CONTRACT,
                            OPENOCEAN_CONTRACTS, PANCAKE_CONTRACTS, SPACEFI_CONTRACTS, SUSHISWAP_CONTRACTS,
                            UNISWAP_CONTRACTS, VELOCORE_CONTRACTS, WOOFI_CONTRACTS, XYSWAP_CONTRACT, TOKENS_PER_CHAIN)
        all_contracts = {
            "iZumi":IZUMI_CONTRACTS,
            "Maverick":MAVERICK_CONTRACTS,
            "Mute":MUTE_CONTRACTS,
            "ODOS":ODOS_CONTRACT,
            "1inch":ONEINCH_CONTRACT,
            "OpenOcean":OPENOCEAN_CONTRACTS,
            "PancakeSwap":PANCAKE_CONTRACTS,
            "SpaceFi":SPACEFI_CONTRACTS,
            "SushiSwap":SUSHISWAP_CONTRACTS,
            "Uniswap":UNISWAP_CONTRACTS,
            "Velocore":VELOCORE_CONTRACTS,
            "WooFi":WOOFI_CONTRACTS,
            "XYfinance":XYSWAP_CONTRACT,
        }

        all_network_contracts = {
            name: contracts[self.network]['router']
            for name, contracts in all_contracts.items()
            if contracts.get(self.network)
        }

        approve_contracts = [(k, v) for k, v in all_network_contracts.items()]
        contract_name, approve_contract = random.choice(approve_contracts)
        native = ['ETH', 'WETH']
        token_contract = random.choice([i for i in list(TOKENS_PER_CHAIN[self.network].items()) if i not in native])
        amount = random.uniform(1, 10000)
        amount_in_wei = int(amount * 10 ** await self.client.get_decimals(token_contract[0]))

        message = f"Approve {amount:.4f} {token_contract[0]} for {contract_name}"
        self.logger_msg(*self.client.acc_info, msg=message)
        return await self.client.check_for_approved(token_contract[1], approve_contract,
                                                    amount_in_wei, without_bal_check=True)


class Scroll(Blockchain, SimpleEVM):
    def __init__(self, client):
        SimpleEVM.__init__(self, client)
        Blockchain.__init__(self, client)
        self.oracle_contract = self.client.get_contract(
            NATIVE_CONTRACTS_PER_CHAIN[self.network]["oracle"],
            NATIVE_ABI[self.network]['oracle'])

    @helper
    @gas_checker
    async def deposit(self):

        amount = await self.client.get_smart_amount(NATIVE_DEPOSIT_AMOUNT)
        amount_in_wei = int(amount * 10 ** 18)

        self.client.logger.info(f'{self.client.info} Bridge {amount} ETH ERC20 -> Scroll')

        if await self.client.w3.eth.get_balance(self.client.address) > amount_in_wei:

            bridge_fee = await self.oracle_contract.functions.estimateCrossDomainMessageFee(168000).call()

            tx_params = await self.client.prepare_transaction(value=amount_in_wei + bridge_fee)

            transaction = await self.deposit_contract.functions.depositETH(
                amount_in_wei,
                168000,
            ).build_transaction(tx_params)

            return await self.client.send_transaction(transaction)

        else:
            raise RuntimeError('Insufficient balance!')

    @helper
    @gas_checker
    async def withdraw(self):

        amount, amount_in_wei = await self.client.check_and_get_eth(NATIVE_WITHDRAW_AMOUNT)

        self.client.logger.info(
            f'{self.client.info} Scroll | Withdraw {amount} ETH Scroll -> ERC20')

        if await self.client.w3.eth.get_balance(self.client.address) > amount_in_wei:

            tx_params = await self.client.prepare_transaction(value=amount_in_wei)

            transaction = await self.withdraw_contract.functions.withdrawETH(
                amount_in_wei,
                0
            ).build_transaction(tx_params)

            return await self.client.send_transaction(transaction)

        else:
            raise RuntimeError('Insufficient balance!')


class ZkSync(Blockchain, SimpleEVM):
    def __init__(self, client):
        SimpleEVM.__init__(self, client)
        Blockchain.__init__(self, client)

        self.deposit_contract = self.client.get_contract(NATIVE_CONTRACTS_PER_CHAIN['zkSync']['deposit'],
                                                         NATIVE_ABI['zkSync']['deposit'])
        self.withdraw_contract = self.client.get_contract(NATIVE_CONTRACTS_PER_CHAIN['zkSync']['withdraw'],
                                                          NATIVE_ABI['zkSync']['withdraw'])
        self.token_contract = self.client.get_contract(TOKENS_PER_CHAIN['zkSync']['WETH'],
                                                       WETH_ABI)

    @helper
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

    @helper
    @gas_checker
    async def withdraw(self):

        amount, amount_in_wei = await self.client.check_and_get_eth(NATIVE_WITHDRAW_AMOUNT)

        self.logger_msg(*self.client.acc_info, msg=f'Withdraw on txSync: {amount} ETH zkSync Era -> ERC20')

        if await self.client.w3.eth.get_balance(self.client.address) > amount_in_wei:

            tx_params = await self.client.prepare_transaction(value=amount_in_wei)

            transaction = await self.withdraw_contract.functions.withdraw(
                self.client.address,
            ).build_transaction(tx_params)

            return await self.client.send_transaction(transaction)

        else:
            raise RuntimeError('Withdraw on txSync | Insufficient balance!')


class StarknetEVM(Blockchain, Logger, Bridge):
    def __init__(self, client):
        Logger.__init__(self)
        Bridge.__init__(self, client)
        Blockchain.__init__(self, client)

        self.evm_contract = self.client.get_contract(NATIVE_CONTRACTS_PER_CHAIN['Starknet']['evm_contract'],
                                                     NATIVE_ABI['Starknet']['evm_contract'])

    async def bridge(self, *args, **kwargs):
        pass

    async def get_starknet_deposit_fee(self, amount_in_wei: int):
        stark_w3 = FullNodeClient(random.choice(StarknetRPC.rpc))
        return (await stark_w3.estimate_message_fee(
            from_address=NATIVE_CONTRACTS_PER_CHAIN['Starknet']['evm_contract'],
            to_address=NATIVE_CONTRACTS_PER_CHAIN['Starknet']['stark_contract'],
            entry_point_selector=get_selector_from_name("handle_deposit"),
            payload=[
                int(self.client.address, 16),
                amount_in_wei,
                0
            ]
        )).overall_fee

    @helper
    @gas_checker
    async def deposit(self, private_keys:dict = None):

        receiver = await self.get_address_for_bridge(private_keys['stark_key'], stark_key_type=True)

        amount = await self.client.get_smart_amount(NATIVE_DEPOSIT_AMOUNT)
        amount_in_wei = int(amount * 10 ** 18)

        self.logger_msg(self.client.account_name, None,
                        msg=f'Bridge on StarkGate to {receiver}: {amount} ETH ERC20 -> Starknet')

        deposit_fee = await self.get_starknet_deposit_fee(amount_in_wei)

        tx_params = await self.client.prepare_transaction(value=amount_in_wei + deposit_fee)

        transaction = await self.evm_contract.functions.deposit(
            amount_in_wei,
            int(receiver, 16)
        ).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)

    async def withdraw(self):
        pass  # реализовано в Starknet


class Base(Blockchain, SimpleEVM):
    def __init__(self, client):
        SimpleEVM.__init__(self, client)
        Blockchain.__init__(self, client)


class Linea(Blockchain, SimpleEVM):
    def __init__(self, client):
        SimpleEVM.__init__(self, client)
        Blockchain.__init__(self, client)


class ArbitrumNova(Blockchain, SimpleEVM):
    def __init__(self, client):
        SimpleEVM.__init__(self, client)
        Blockchain.__init__(self, client)


class Zora(Blockchain, SimpleEVM):
    def __init__(self, client):
        SimpleEVM.__init__(self, client)
        Blockchain.__init__(self, client)
