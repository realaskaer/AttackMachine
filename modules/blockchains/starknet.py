import os
import time

from starknet_py.hash.selector import get_selector_from_name
from starknet_py.net.models import StarknetChainId

from modules import Blockchain
from utils.stark_signature.stark_deployer import BraavosCurveSigner
from utils.tools import repeater, gas_checker
from settings import NATIVE_WITHDRAW_AMOUNT, TRANSFER_AMOUNT, USE_PROXY
from config import (NATIVE_CONTRACTS_PER_CHAIN, NATIVE_ABI, SPACESHARD_CONTRACT, TOKENS_PER_CHAIN,
                    ARGENT_IMPLEMENTATION_CLASS_HASH_NEW, BRAAVOS_PROXY_CLASS_HASH,
                    BRAAVOS_IMPLEMENTATION_CLASS_HASH_NEW, BRAAVOS_IMPLEMENTATION_CLASS_HASH)


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
            await self.client.initialize_account(check_balance=True)

            if self.client.WALLET_TYPE:
                self.client.account.signer = BraavosCurveSigner(
                    account_address=self.client.account.address,
                    key_pair=self.client.key_pair,
                    chain_id=self.client.chain_id
                )

                class_hash = BRAAVOS_PROXY_CLASS_HASH
                salt = [self.client.key_pair.public_key]
                selector = get_selector_from_name("initializer")
                constructor_calldata = [BRAAVOS_IMPLEMENTATION_CLASS_HASH, selector, len(salt), *salt]

                self.client.logger.info(f"{self.client.info} Deploy Braavos account")
            else:

                self.client.logger.info(f"{self.client.info} Deploy ArgentX account")

                class_hash = ARGENT_IMPLEMENTATION_CLASS_HASH_NEW
                constructor_calldata = [self.client.key_pair.public_key, 0]

            signed_tx = await self.client.account.sign_deploy_account_transaction(
                class_hash=class_hash,
                contract_address_salt=self.client.key_pair.public_key,
                constructor_calldata=constructor_calldata,
                nonce=0,
                auto_estimate=True
            )

            tx_hash = (await self.client.account.client.deploy_account(signed_tx)).transaction_hash
            return await self.client.send_transaction(check_hash=True, hash_for_check=tx_hash)
        finally:
            if USE_PROXY:
                await self.client.session.close()

    @repeater
    @gas_checker
    async def upgrade_wallet(self):
        try:
            await self.client.initialize_account()

            wallets_name = {
                1: 'Braavos',
                0: 'ArgentX'
            }

            wallet_name, wallet_type = wallets_name[self.client.WALLET_TYPE], self.client.WALLET_TYPE

            implementation_version = (await self.client.account.client.call_contract(self.client.prepare_call(
                contract_address=self.client.address,
                selector_name="get_implementation",
                calldata=[]
            )))[0] if wallet_type else await self.client.account.client.get_class_hash_at(self.client.account.address)

            braavos_hash, argent_hash = BRAAVOS_IMPLEMENTATION_CLASS_HASH_NEW, ARGENT_IMPLEMENTATION_CLASS_HASH_NEW

            implement_hash = braavos_hash if wallet_type else argent_hash
            upgrade_data = [int(implement_hash)] if wallet_type else [int(implement_hash), 1, 0]

            if implementation_version != implement_hash:
                self.client.logger.info(f"{self.client.info} Upgrade {wallet_name.capitalize()} account")

                upgrade_call = self.client.prepare_call(
                    contract_address=self.client.address,
                    selector_name='upgrade',
                    calldata=upgrade_data
                )

                return await self.client.send_transaction(upgrade_call)
            else:
                self.client.logger.warning(f"{self.client.info} Account already upgraded!")
        finally:
            if USE_PROXY:
                await self.client.session.close()

