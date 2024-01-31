import random

from web3.exceptions import Web3ValidationError

from modules import Refuel, Logger
from eth_abi import abi
from decimal import Decimal

from modules.interfaces import BlockchainException, SoftwareException, BlockchainExceptionWithoutRetry
from settings import DST_CHAIN_MERKLY_REFUEL, DST_CHAIN_MERKLY_WORMHOLE, WORMHOLE_TOKENS_AMOUNT
from utils.tools import gas_checker, helper, sleep
from config import (
    MERKLY_CONTRACTS_PER_CHAINS,
    MERKLY_ABI,
    LAYERZERO_NETWORKS_DATA, MERKLY_NFT_WORMHOLE_INFO, MERKLY_WRAPPED_NETWORK,
    MERKLY_TOKENS_WORMHOLE_INFO, LAYERZERO_WRAPED_NETWORKS
)


class Merkly(Refuel, Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)

    async def get_nft_id(self, tx_hash: bytes):
        tx_receipt = await self.client.w3.eth.get_transaction_receipt(tx_hash)

        return int((tx_receipt.logs[0].topics[3]).hex(), 16)

    @helper
    @gas_checker
    async def refuel(self, chain_from_id, attack_mode: bool = False, attack_data: dict = None, need_check:bool = False):
        if not attack_mode and attack_data is None:
            dst_data = random.choice(list(DST_CHAIN_MERKLY_REFUEL.items()))
        else:
            dst_data = random.choice(list(attack_data.items()))

        dst_chain_name, dst_chain_id, dst_native_name, dst_native_api_name = LAYERZERO_NETWORKS_DATA[dst_data[0]]
        dst_amount = self.client.round_amount(*dst_data[1])

        if not need_check:
            refuel_info = f'{dst_amount} {dst_native_name} to {dst_chain_name} from {self.client.network.name}'
            self.logger_msg(*self.client.acc_info, msg=f'Refuel on Merkly: {refuel_info}')

        merkly_contracts = MERKLY_CONTRACTS_PER_CHAINS[chain_from_id]

        refuel_contract = self.client.get_contract(merkly_contracts['refuel'], MERKLY_ABI['refuel'])

        dst_native_gas_amount = int(dst_amount * 10 ** 18)
        dst_contract_address = MERKLY_CONTRACTS_PER_CHAINS[LAYERZERO_WRAPED_NETWORKS[dst_data[0]]]['refuel']

        gas_limit = await refuel_contract.functions.minDstGasLookup(dst_chain_id, 0).call()

        if gas_limit == 0 and not need_check:
            raise SoftwareException('This refuel path is not active!')

        adapter_params = abi.encode(["uint16", "uint64", "uint256"],
                                    [2, gas_limit, dst_native_gas_amount])

        adapter_params = self.client.w3.to_hex(adapter_params[30:]) + self.client.address[2:].lower()

        try:
            estimate_send_fee = (await refuel_contract.functions.estimateSendFee(
                dst_chain_id,
                dst_contract_address,
                adapter_params
            ).call())[0]

            transaction = await refuel_contract.functions.bridgeGas(
                dst_chain_id,
                self.client.address,
                adapter_params
            ).build_transaction(await self.client.prepare_transaction(value=estimate_send_fee))

            if need_check:
                return True

            tx_hash = await self.client.send_transaction(transaction, need_hash=True)

            result = False
            if isinstance(tx_hash, bytes):
                if self.client.network.name != 'Polygon':
                    result = await self.client.wait_for_l0_received(tx_hash)
            else:
                result = tx_hash

            if attack_data and attack_mode is False:
                return LAYERZERO_WRAPED_NETWORKS[chain_from_id], dst_chain_id
            return result

        except Web3ValidationError:
            if not need_check:
                raise BlockchainExceptionWithoutRetry(f'Problem to validate ABI function')

        except Exception as error:
            if not need_check:
                raise BlockchainException(f'{error}')

    @helper
    @gas_checker
    async def mint(self, chain_id_from):
        onft_contract = self.client.get_contract(MERKLY_CONTRACTS_PER_CHAINS[chain_id_from]['ONFT'], MERKLY_ABI['ONFT'])

        mint_price = await onft_contract.functions.fee().call()

        self.logger_msg(
            *self.client.acc_info,
            msg=f"Mint Merkly NFT on {self.client.network.name}. "
                f"Gas Price: {(mint_price / 10 ** 18):.5f} {self.client.network.token}")

        tx_params = await self.client.prepare_transaction(value=mint_price)

        transaction = await onft_contract.functions.mint().build_transaction(tx_params)

        return await self.client.send_transaction(transaction)

    @helper
    @gas_checker
    async def mint_and_bridge_wormhole_nft(self, chain_id_from):

        onft_contract = self.client.get_contract(
            MERKLY_CONTRACTS_PER_CHAINS[chain_id_from]['WNFT'], MERKLY_ABI['WNFT'])

        dst_chain = random.choice(DST_CHAIN_MERKLY_WORMHOLE)
        _, _, mint_price, _ = MERKLY_NFT_WORMHOLE_INFO[chain_id_from]
        dst_chain_name, wnft_contract, _, wormhole_id = MERKLY_NFT_WORMHOLE_INFO[MERKLY_WRAPPED_NETWORK[dst_chain]]

        estimate_fee = (await onft_contract.functions.quoteBridge(
            wormhole_id,
            0,
            200000
        ).call())[0]

        mint_price_in_wei = int(Decimal(f"{mint_price}") * 10 ** 18)

        self.logger_msg(
            *self.client.acc_info,
            msg=f"Mint NFT on Merkly Wormhole. Network: {self.client.network.name}."
                f" Price for mint: {mint_price} {self.client.network.token}")

        transaction = await onft_contract.functions.mint(
            1
        ).build_transaction(await self.client.prepare_transaction(value=mint_price_in_wei))

        tx_hash = await self.client.send_transaction(transaction, need_hash=True)

        nft_id = await self.get_nft_id(tx_hash)

        await sleep(self, 5, 8)

        self.logger_msg(
            *self.client.acc_info,
            msg=f"Bridge NFT on Merkly Wormhole from {self.client.network.name} -> {dst_chain_name}."
                f" Price for bridge: "
                f"{(estimate_fee / 10 ** 18):.6f} {self.client.network.token}")

        transaction = await onft_contract.functions.transferNFT(
            wormhole_id,
            wnft_contract,
            nft_id,
            0,
            200000,
            wormhole_id,
            self.client.address
        ).build_transaction(await self.client.prepare_transaction(value=estimate_fee))

        return await self.client.send_transaction(transaction)

    @helper
    @gas_checker
    async def mint_and_bridge_wormhole_tokens(self, chain_id_from):
        tokens_amount = WORMHOLE_TOKENS_AMOUNT

        onft_contract = self.client.get_contract(
            MERKLY_CONTRACTS_PER_CHAINS[chain_id_from]['WOFT'], MERKLY_ABI['WOFT'])

        dst_chain = random.choice(DST_CHAIN_MERKLY_WORMHOLE)
        _, _, mint_price, _ = MERKLY_TOKENS_WORMHOLE_INFO[chain_id_from]
        dst_chain_name, woft_contract, _, wormhole_id = MERKLY_TOKENS_WORMHOLE_INFO[MERKLY_WRAPPED_NETWORK[dst_chain]]

        estimate_fee = (await onft_contract.functions.quoteBridge(
            wormhole_id,
            0,
            200000
        ).call())[0]

        mint_price_in_wei = int((Decimal(f"{mint_price}") * 10 ** 18) * tokens_amount)

        self.logger_msg(
            *self.client.acc_info,
            msg=f"Mint {tokens_amount} WMEKL on Merkly Wormhole. Network: {self.client.network.name}."
                f" Price for mint: {mint_price * tokens_amount:.6f} {self.client.network.token}")

        transaction = await onft_contract.functions.mint(
            self.client.address,
            tokens_amount
        ).build_transaction(await self.client.prepare_transaction(value=mint_price_in_wei))

        await self.client.send_transaction(transaction)

        await sleep(self, 5, 8)

        self.logger_msg(
            *self.client.acc_info,
            msg=f"Bridge tokens on Merkly Wormhole from {self.client.network.name} -> {dst_chain_name}."
                f" Price for bridge: {(estimate_fee / 10 ** 18):.6f} {self.client.network.token}")

        transaction = await onft_contract.functions.bridge(
            wormhole_id,
            woft_contract,
            tokens_amount,
            0,
            200000,
            wormhole_id,
            self.client.address
        ).build_transaction(await self.client.prepare_transaction(value=estimate_fee))

        return await self.client.send_transaction(transaction)
