import random

from eth_typing import HexStr
from modules import Refuel, Logger, Client
from eth_abi import abi
from decimal import Decimal

from modules.interfaces import BlockchainException, SoftwareException, Minter
from utils.tools import helper, sleep
from config import (
    MERKLY_CONTRACTS_PER_CHAINS,
    MERKLY_ABI,
    LAYERZERO_NETWORKS_DATA, MERKLY_NFT_WORMHOLE_INFO, MERKLY_WRAPPED_NETWORK,
    MERKLY_TOKENS_WORMHOLE_INFO, LAYERZERO_WRAPED_NETWORKS, ZERO_ADDRESS, CHAIN_NAME, CHAIN_IDS
)


class Merkly(Refuel, Minter, Logger):
    def __init__(self, client: Client):
        self.client = client
        Logger.__init__(self)

    async def get_nft_id(self, tx_hash: HexStr):
        tx_receipt = await self.client.w3.eth.get_transaction_receipt(tx_hash)

        if self.client.network.name == 'zkSync':
            nft_id = int((tx_receipt.logs[2].topics[3]).hex(), 16)
            if not nft_id:
                nft_id = int((tx_receipt.logs[3].topics[3]).hex(), 16)
        elif self.client.network.name == 'Polygon':
            nft_id = int((tx_receipt.logs[1].topics[3]).hex(), 16)
        else:
            nft_id = int((tx_receipt.logs[0].topics[3]).hex(), 16)
        return nft_id

    async def get_estimate_send_fee(self, contract, adapter_params, dst_chain_id, nft_id):
        estimate_gas_bridge_fee = (await contract.functions.estimateSendFee(
            dst_chain_id,
            self.client.address,
            nft_id,
            False,
            adapter_params
        ).call())[0]

        return estimate_gas_bridge_fee

    async def mint(self, chain_id_from, onft_contract):
        mint_price = await onft_contract.functions.fee().call()
        nft_name = await onft_contract.functions.name().call()

        self.logger_msg(
            *self.client.acc_info,
            msg=f"Mint {nft_name} NFT on {self.client.network.name}. "
                f"Price: {(mint_price / 10 ** 18):.5f} {self.client.network.token}")

        tx_params = await self.client.prepare_transaction(value=mint_price)
        transaction = await onft_contract.functions.mint().build_transaction(tx_params)

        return await self.client.send_transaction(transaction, need_hash=True)

    @helper
    async def refuel(
            self, chain_from_id: int, attack_data: dict, google_mode:bool = False, need_check:bool = False
    ):
        dst_data = random.choice(list(attack_data.items()))
        dst_chain_name, dst_chain_id, dst_native_name, dst_native_api_name = LAYERZERO_NETWORKS_DATA[dst_data[0]]
        dst_amount = await self.client.get_smart_amount(dst_data[1])

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

            tx_result = await self.client.send_transaction(transaction, need_hash=True)

            result = True
            if isinstance(tx_result, bool):
                result = tx_result
            else:
                if self.client.network.name != 'Polygon':
                    result = await self.client.wait_for_l0_received(tx_result)

            if google_mode:
                return LAYERZERO_WRAPED_NETWORKS[chain_from_id], dst_chain_id
            return result

        except Exception as error:
            if not need_check:
                raise BlockchainException(f'{error}')

    @helper
    async def bridge(
            self, chain_from_id: int, attack_data: int, google_mode:bool = False, need_check:bool = False
    ):
        onft_contract = self.client.get_contract(MERKLY_CONTRACTS_PER_CHAINS[chain_from_id]['ONFT'], MERKLY_ABI['ONFT'])
        dst_chain_name, dst_chain_id, _, _ = LAYERZERO_NETWORKS_DATA[attack_data]

        if not need_check:
            tx_hash = await self.mint(chain_from_id, onft_contract)
            nft_id = await self.get_nft_id(tx_hash)
            await sleep(self, 5, 10)

            self.logger_msg(
                *self.client.acc_info,
                msg=f"Bridge Merkly NFT from {self.client.network.name} to {dst_chain_name}. ID: {nft_id}")
        else:
            nft_id = await onft_contract.functions.nextMintId().call()

        version, gas_limit = 1, 200000

        adapter_params = abi.encode(["uint16", "uint256"],
                                    [version, gas_limit])

        adapter_params = self.client.w3.to_hex(adapter_params[30:])

        try:
            estimate_send_fee = await self.get_estimate_send_fee(onft_contract, adapter_params, dst_chain_id, nft_id)

            if need_check:
                if await self.client.w3.eth.get_balance(self.client.address) > estimate_send_fee:
                    return True
                return False

            tx_params = await self.client.prepare_transaction(value=estimate_send_fee)

            transaction = await onft_contract.functions.sendFrom(
                self.client.address,
                dst_chain_id,
                self.client.address,
                nft_id,
                self.client.address,
                ZERO_ADDRESS,
                adapter_params
            ).build_transaction(tx_params)

            tx_result = await self.client.send_transaction(transaction, need_hash=True)

            result = True
            if isinstance(tx_result, bool):
                result = tx_result
            else:
                if self.client.network.name != 'Polygon':
                    result = await self.client.wait_for_l0_received(tx_result)

            if google_mode:
                return LAYERZERO_WRAPED_NETWORKS[chain_from_id], dst_chain_id
            return result

        except Exception as error:
            if not need_check:
                raise BlockchainException(f'{error}')

    @helper
    async def wnft_bridge(
            self, chain_from_id: int, attack_data: int, google_mode:bool = False, need_check:bool = False
    ):

        onft_contract = self.client.get_contract(
            MERKLY_CONTRACTS_PER_CHAINS[chain_from_id]['WNFT'], MERKLY_ABI['WNFT'])

        _, _, mint_price, _ = MERKLY_NFT_WORMHOLE_INFO[chain_from_id]
        dst_chain_name, wnft_contract, _, wormhole_id = MERKLY_NFT_WORMHOLE_INFO[MERKLY_WRAPPED_NETWORK[attack_data]]

        estimate_fee = (await onft_contract.functions.quoteBridge(
            wormhole_id,
            0,
            200000
        ).call())[0]

        mint_price_in_wei = int(Decimal(f"{mint_price}") * 10 ** 18)

        if not need_check:
            self.logger_msg(
                *self.client.acc_info,
                msg=f"Mint NFT on Merkly Wormhole. Network: {self.client.network.name}."
                    f" Price for mint: {mint_price} {self.client.network.token}")

        try:
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

            if need_check:
                return True

            if google_mode:
                return chain_from_id, attack_data
            return await self.client.send_transaction(transaction)

        except Exception as error:
            if not need_check:
                raise BlockchainException(f'{error}')

    @helper
    async def wt_bridge(
            self, chain_from_id:int, attack_data:tuple, google_mode:bool = False, need_check:bool = False
    ):
        tokens_amount_mint, tokens_amount_bridge, dst_chain = attack_data

        oft_contract = self.client.get_contract(
            MERKLY_CONTRACTS_PER_CHAINS[chain_from_id]['WOFT'], MERKLY_ABI['WOFT'])

        _, _, mint_price, _ = MERKLY_TOKENS_WORMHOLE_INFO[chain_from_id]
        dst_chain_name, woft_contract, _, wormhole_id = MERKLY_TOKENS_WORMHOLE_INFO[MERKLY_WRAPPED_NETWORK[dst_chain]]

        estimate_fee = (await oft_contract.functions.quoteBridge(
            wormhole_id,
            0,
            200000
        ).call())[0]

        token_balance = round((await oft_contract.functions.balanceOf(self.client.address).call()) / 10 ** 18)

        if (token_balance == 0 and need_check) or (token_balance < tokens_amount_bridge and not need_check):

            mint_price_in_wei = int(mint_price * tokens_amount_mint * 10 ** 18)

            self.logger_msg(
                *self.client.acc_info,
                msg=f"Mint {tokens_amount_mint} WMEKL on Merkly Wormhole. Network: {self.client.network.name}."
                    f" Price for mint: {mint_price * tokens_amount_mint:.6f} {self.client.network.token}")

            transaction = await oft_contract.functions.mint(
                self.client.address,
                tokens_amount_mint
            ).build_transaction(await self.client.prepare_transaction(value=mint_price_in_wei))

            await self.client.send_transaction(transaction)

            await sleep(self, 5, 8)
        else:
            if not need_check:
                self.logger_msg(
                    *self.client.acc_info,
                    msg=f"Have enough WMEKL balance: {token_balance}. Network: {self.client.network.name}",
                    type_msg='success')

        if not need_check:
            self.logger_msg(
                *self.client.acc_info,
                msg=f"Bridge tokens on Merkly Wormhole from {self.client.network.name} -> {dst_chain_name}."
                    f" Price for bridge: {(estimate_fee / 10 ** 18):.6f} {self.client.network.token}")
        try:
            transaction = await oft_contract.functions.bridge(
                wormhole_id,
                woft_contract,
                int(tokens_amount_bridge * 10 ** 18),
                0,
                200000,
                wormhole_id,
                self.client.address
            ).build_transaction(await self.client.prepare_transaction(value=estimate_fee))

            if need_check:
                return True

            if google_mode:
                return chain_from_id, dst_chain
            return await self.client.send_transaction(transaction)

        except Exception as error:
            if not need_check:
                raise BlockchainException(f'{error}')

    @helper
    async def pnft_bridge(
            self, chain_from_id: int, attack_data: int, google_mode: bool = False, need_check: bool = False
    ):
        onft_contract = self.client.get_contract(MERKLY_CONTRACTS_PER_CHAINS[chain_from_id]['PNFT'], MERKLY_ABI['ONFT'])
        dst_chain_name, dst_chain_id, _, _ = LAYERZERO_NETWORKS_DATA[attack_data]

        mint_price = await onft_contract.functions.fee().call()

        if need_check and await self.client.w3.eth.get_balance(self.client.address) > mint_price:
            return True

        tx_hash = await self.mint(chain_from_id, onft_contract)
        nft_id = await self.get_nft_id(tx_hash)
        await sleep(self, 5, 10)

        self.logger_msg(
            *self.client.acc_info,
            msg=f"Bridge zkMerkly NFT from {self.client.network.name} to {dst_chain_name}. ID: {nft_id}")

        version, gas_limit = 1, 200000

        adapter_params = abi.encode(["uint16", "uint256"],
                                    [version, gas_limit])

        adapter_params = self.client.w3.to_hex(adapter_params[30:])

        try:
            estimate_send_fee = await self.get_estimate_send_fee(onft_contract, adapter_params, dst_chain_id, nft_id)

            tx_params = await self.client.prepare_transaction(value=int(estimate_send_fee))

            transaction = await onft_contract.functions.sendFrom(
                self.client.address,
                dst_chain_id,
                self.client.address,
                nft_id,
                self.client.address,
                ZERO_ADDRESS,
                adapter_params
            ).build_transaction(tx_params)

            tx_result = await self.client.send_transaction(transaction, need_hash=True)

            result = True
            if isinstance(tx_result, bool):
                result = tx_result
            else:
                if self.client.network.name != 'Polygon':
                    result = await self.client.wait_for_l0_received(tx_result)

            if google_mode:
                return LAYERZERO_WRAPED_NETWORKS[chain_from_id], dst_chain_id
            return result

        except Exception as error:
            if not need_check:
                raise BlockchainException(f'{error}')

    @helper
    async def p_refuel(
            self, chain_from_id: int, attack_data: dict, google_mode: bool = False, need_check: bool = False
    ):
        dst_data = random.choice(list(attack_data.items()))
        dst_chain_name, dst_chain_id, dst_native_name, dst_native_api_name = LAYERZERO_NETWORKS_DATA[dst_data[0]]
        dst_amount = self.client.round_amount(*dst_data[1])

        if not need_check:
            refuel_info = f'{dst_amount} {dst_native_name} to {dst_chain_name} from {self.client.network.name}'
            self.logger_msg(*self.client.acc_info, msg=f'Refuel on Merkly Polyhedra: {refuel_info}')

        merkly_contracts = MERKLY_CONTRACTS_PER_CHAINS[chain_from_id]

        refuel_contract = self.client.get_contract(merkly_contracts['p_refuel'], MERKLY_ABI['refuel'])

        dst_native_gas_amount = int(dst_amount * 10 ** 18)
        dst_contract_address = MERKLY_CONTRACTS_PER_CHAINS[LAYERZERO_WRAPED_NETWORKS[dst_data[0]]]['p_refuel']

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

            tx_result = await self.client.send_transaction(transaction, need_hash=True)

            result = True
            if isinstance(tx_result, bool):
                result = tx_result
            else:
                if self.client.network.name != 'Polygon':
                    result = await self.client.wait_for_l0_received(tx_result)

            if google_mode:
                return LAYERZERO_WRAPED_NETWORKS[chain_from_id], dst_chain_id
            return result

        except Exception as error:
            if not need_check:
                raise BlockchainException(f'{error}')

    @helper
    async def hnft_bridge(
            self, chain_from_id: int, attack_data: int, google_mode: bool = False, need_check: bool = False
    ):
        onft_contract = self.client.get_contract(MERKLY_CONTRACTS_PER_CHAINS[chain_from_id]['HNFT'], MERKLY_ABI['HNFT'])
        dst_chain_name = CHAIN_NAME[MERKLY_WRAPPED_NETWORK[attack_data]]
        dst_chain_id = CHAIN_IDS[MERKLY_WRAPPED_NETWORK[attack_data]]

        estimate_fee = (await onft_contract.functions.quoteBridge(
            dst_chain_id
        ).call())

        mint_price = await onft_contract.functions.fee().call()

        if (await self.client.w3.eth.get_balance(self.client.address) > estimate_fee + mint_price) and need_check:
            return True
        elif need_check:
            return False

        self.logger_msg(
            *self.client.acc_info,
            msg=f"Mint NFT on Merkly Hyperlane. Network: {self.client.network.name}."
                f" Price for mint: {mint_price / 10 ** 18:5f} {self.client.network.token}")

        transaction = await onft_contract.functions.mint(
            1
        ).build_transaction(await self.client.prepare_transaction(value=mint_price))

        tx_hash = await self.client.send_transaction(transaction, need_hash=True)

        nft_id = await self.get_nft_id(tx_hash)

        await sleep(self, 5, 8)

        self.logger_msg(
            *self.client.acc_info,
            msg=f"Bridge NFT on Merkly Hyperlane from {self.client.network.name} -> {dst_chain_name}."
                f" Price for bridge: "
                f"{(estimate_fee / 10 ** 18):.6f} {self.client.network.token}")

        transaction = await onft_contract.functions.bridgeNFT(
            dst_chain_id,
            nft_id
        ).build_transaction(await self.client.prepare_transaction(value=estimate_fee))

        if need_check:
            return True

        if google_mode:
            return chain_from_id, attack_data
        return await self.client.send_transaction(transaction)

    @helper
    async def ht_bridge(
            self, chain_from_id:int, attack_data:tuple, google_mode:bool = False, need_check:bool = False
    ):
        tokens_amount_mint, tokens_amount_bridge, dst_chain = attack_data
        oft_contract = self.client.get_contract(MERKLY_CONTRACTS_PER_CHAINS[chain_from_id]['HOFT'], MERKLY_ABI['HOFT'])
        dst_chain_name = CHAIN_NAME[MERKLY_WRAPPED_NETWORK[dst_chain]]
        dst_chain_id = CHAIN_IDS[MERKLY_WRAPPED_NETWORK[dst_chain]]

        estimate_fee = await oft_contract.functions.quoteBridge(
            dst_chain_id,
        ).call()

        mint_price = (await oft_contract.functions.fee().call()) * tokens_amount_mint

        if (await self.client.w3.eth.get_balance(self.client.address) > estimate_fee + mint_price) and need_check:
            return True
        elif need_check:
            return False

        token_balance = round((await oft_contract.functions.balanceOf(self.client.address).call()) / 10 ** 18)

        if (token_balance == 0 and need_check) or (token_balance < tokens_amount_bridge and not need_check):

            self.logger_msg(
                *self.client.acc_info,
                msg=f"Mint {tokens_amount_mint} HMEKL on Merkly Hyperlane. Network: {self.client.network.name}."
                    f" Price for mint: {mint_price / 10 ** 18:.6f} {self.client.network.token}")

            transaction = await oft_contract.functions.mint(
                self.client.address,
                tokens_amount_mint
            ).build_transaction(await self.client.prepare_transaction(value=mint_price))

            await self.client.send_transaction(transaction)

            await sleep(self, 5, 8)
        else:
            self.logger_msg(
                *self.client.acc_info,
                msg=f"Have enough HMEKL balance: {token_balance}. Network: {self.client.network.name}",
                type_msg='success')

        self.logger_msg(
            *self.client.acc_info,
            msg=f"Bridge tokens on Merkly Hyperlane from {self.client.network.name} -> {dst_chain_name}."
                f" Price for bridge: {(estimate_fee / 10 ** 18):.6f} {self.client.network.token}")

        transaction = await oft_contract.functions.bridgeHFT(
            dst_chain_id,
            int(tokens_amount_bridge * 10 ** 18)
        ).build_transaction(await self.client.prepare_transaction(value=estimate_fee))

        if google_mode:
            return chain_from_id, dst_chain
        return await self.client.send_transaction(transaction)
