import os
import time
from starknet_py.net.models import StarknetChainId

from modules import Blockchain
from utils.stark_signature.stark_deployer import BraavosCurveSigner
from utils.tools import repeater, gas_checker
from settings import NATIVE_WITHDRAW_AMOUNT, TRANSFER_AMOUNT, USE_PROXY
from config import (NATIVE_CONTRACTS_PER_CHAIN, NATIVE_ABI, SPACESHARD_CONTRACT, TOKENS_PER_CHAIN,
                    ARGENT_IMPLEMENTATION_CLASS_HASH_NEW, BRAAVOS_PROXY_CLASS_HASH,
                    BRAAVOS_IMPLEMENTATION_CLASS_HASH_NEW)


class Starknet(Blockchain):
    async def deposit(self):
        # реализован в blockchain/StarknetEVM
        pass

    async def wrap_eth(self):
        # не поддерживается в Starknet
        pass

    async def unwrap_eth(self):
        # не поддерживается в Starknet
        pass

    @repeater
    @gas_checker
    async def withdraw(self, receiver):
        try:
            await self.client.initialize_account()

            amount = await self.client.get_smart_amount(NATIVE_WITHDRAW_AMOUNT)
            amount_in_wei = int(amount * 10 ** 18)

            stark_contract_address = NATIVE_CONTRACTS_PER_CHAIN['Starknet']['stark_contract']
            url = f"https://starkgate.spaceshard.io/v1/gas-cost/{stark_contract_address}/{str(int(time.time()))}"

            self.client.logger.info(
                f'{self.client.info} Withdraw on StarkGate to {receiver}: {amount} ETH Starknet -> ERC20')

            transfer_gas_fee = int((await self.make_request(method='GET', url=url))["result"]["gasCost"])

            transfer_call = self.client.prepare_call(
                contract_address=TOKENS_PER_CHAIN['Starknet']['ETH'],
                selector_name="transfer",
                calldata=[
                    SPACESHARD_CONTRACT['core'],
                    transfer_gas_fee, 0
                ]
            )

            withdraw_call = self.client.prepare_call(
                contract_address=NATIVE_CONTRACTS_PER_CHAIN['Starknet']['stark_contract'],
                selector_name="initiate_withdraw",
                calldata=[
                    int(receiver, 16),
                    amount_in_wei, 0
                ]
            )

            return await self.client.send_transaction(transfer_call, withdraw_call)
        finally:
            if USE_PROXY:
                await self.client.session.close()

    @repeater
    @gas_checker
    async def transfer_eth(self):
        try:
            await self.client.initialize_account()

            amount, amount_in_wei = await self.client.check_and_get_eth_for_deposit(TRANSFER_AMOUNT)

            self.client.logger.info(f'{self.client.info} Transfer ETH to random Starknet address: {amount} ETH')

            transfer_call = self.client.prepare_call(
                contract_address=TOKENS_PER_CHAIN['Starknet']['ETH'],
                selector_name="transfer",
                calldata=[
                    int(os.urandom(32).hex(),16),
                    amount_in_wei, 0
                ]
            )

            return await self.client.send_transaction(transfer_call)
        finally:
            if USE_PROXY:
                await self.client.session.close()

    @repeater
    @gas_checker
    async def transfer_eth_to_myself(self):
        try:
            await self.client.initialize_account()

            amount, amount_in_wei = await self.client.check_and_get_eth_for_deposit(TRANSFER_AMOUNT)

            self.client.logger.info(
                f"{self.client.info} Transfer {amount} ETH to your own address")

            transfer_call = self.client.prepare_call(
                contract_address=TOKENS_PER_CHAIN['Starknet']['ETH'],
                selector_name="transfer",
                calldata=[
                    int(self.client.address, 16),
                    amount_in_wei, 0
                ]
            )

            return await self.client.send_transaction(transfer_call)
        finally:
            if USE_PROXY:
                await self.client.session.close()

    @repeater
    @gas_checker
    async def deploy_wallet(self):
        try:
            await self.client.initialize_account()

            _, wallet_type = await self.client.check_wallet_type()

            if wallet_type:
                self.client.account.signer = BraavosCurveSigner(
                    account_address=self.client.account.address,
                    key_pair=self.client.key_pair,
                    chain_id=self.client.chain_id
                )
                class_hash = BRAAVOS_PROXY_CLASS_HASH

                self.client.logger.info(f"{self.client.info} Deploy Braavos account")
            else:

                self.client.logger.info(f"{self.client.info} Deploy ArgentX account")

                class_hash = ARGENT_IMPLEMENTATION_CLASS_HASH_NEW

            tx_hash = (await self.client.account.deploy_account(
                address=self.client.address,
                class_hash=class_hash,
                salt=self.client.key_pair.public_key,
                key_pair=self.client.key_pair,
                client=self.client.account.client,
                chain=StarknetChainId.MAINNET,
                auto_estimate=True
            )).hash

            return await self.client.send_transaction(check_hash=True, hash_for_check=tx_hash)
        finally:
            if USE_PROXY:
                await self.client.session.close()

    @repeater
    @gas_checker
    async def upgrade_wallet(self):
        try:
            await self.client.initialize_account()

            wallet_name, wallet_type = await self.client.check_wallet_type()

            wallet_contract = await self.client.get_contract(self.client.address, NATIVE_ABI['Starknet'][wallet_name])
            implementation_version = await wallet_contract.functions["get_implementation"].call()

            implement_hash = BRAAVOS_IMPLEMENTATION_CLASS_HASH_NEW if wallet_type else ARGENT_IMPLEMENTATION_CLASS_HASH_NEW
            upgrade_data = [implement_hash] if wallet_type else [implement_hash, [0]]

            if implementation_version != implement_hash:
                self.client.logger.info(f"{self.client.info} Upgrade {wallet_name.capitalize()} account")

                upgrade_call = wallet_contract.functions["upgrade"].prepare(*upgrade_data)

                return await self.client.send_transaction(upgrade_call)
            else:
                self.client.logger.warning(f"{self.client.info} Account already upgraded!")
        finally:
            if USE_PROXY:
                await self.client.session.close()

