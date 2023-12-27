import random

from modules import Refuel, Logger
from eth_abi import abi
from settings import DST_CHAIN_MERKLY_REFUEL, DST_CHAIN_MERKLY_WORMHOLE, SRC_CHAIN_MERKLY
from utils.tools import gas_checker, helper, sleep
from config import (
    MERKLY_CONTRACTS_PER_CHAINS,
    MERKLY_ABI,
    LAYERZERO_NETWORKS_DATA, CHAIN_NAME, MERKLY_WORMHOLE_INFO, LAYERZERO_WRAPED_NETWORKS, MERKLY_WRAPPED_NETWORK
)


class Merkly(Refuel, Logger):
    def __init__(self, client):
        super().__init__()
        self.client = client

    async def get_nft_id(self, tx_hash: bytes):
        tx_receipt = await self.client.w3.eth.get_transaction_receipt(tx_hash)

        return int((tx_receipt.logs[0].topics[3]).hex(), 16)

    @helper
    @gas_checker
    async def refuel(self, chain_from_id, attack_mode:bool = False, attack_data:dict = False):
        if not attack_mode:
            dst_data = random.choice(list(DST_CHAIN_MERKLY_REFUEL.items()))
        else:
            dst_data = random.choice(list(attack_data.items()))

        dst_chain_name, dst_chain_id, dst_native_name, dst_native_api_name = LAYERZERO_NETWORKS_DATA[dst_data[0]]
        dst_amount = self.client.round_amount(*dst_data[1])

        merkly_contracts = MERKLY_CONTRACTS_PER_CHAINS[chain_from_id]

        refuel_contract = self.client.get_contract(merkly_contracts['refuel'], MERKLY_ABI['refuel'])

        refuel_info = f'{dst_amount} {dst_native_name} from {CHAIN_NAME[chain_from_id]} to {dst_chain_name}'
        self.logger_msg(*self.client.acc_info, msg=f'Refuel on Merkly: {refuel_info}')

        dst_native_gas_amount = int(dst_amount * 10 ** 18)
        dst_contract_address = merkly_contracts['refuel']

        gas_limit = await refuel_contract.functions.minDstGasLookup(dst_chain_id, 0).call()

        adapter_params = abi.encode(["uint16", "uint64", "uint256"],
                                    [2, gas_limit, dst_native_gas_amount])

        adapter_params = self.client.w3.to_hex(adapter_params[30:]) + self.client.address[2:].lower()

        estimate_send_fee = (await refuel_contract.functions.estimateSendFee(
            dst_chain_id,
            dst_contract_address,
            adapter_params
        ).call())[0]

        value = estimate_send_fee

        tx_params = await self.client.prepare_transaction(value=value)

        transaction = await refuel_contract.functions.bridgeGas(
            dst_chain_id,
            self.client.address,
            adapter_params
        ).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)

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
    async def mint_and_bridge_wormhole(self, chain_id_from):

        onft_contract = self.client.get_contract(
            MERKLY_CONTRACTS_PER_CHAINS[chain_id_from]['WNFT'], MERKLY_ABI['WNFT'])

        dst_chain = random.choice(DST_CHAIN_MERKLY_WORMHOLE)
        _, _, mint_price, _ = MERKLY_WORMHOLE_INFO[chain_id_from]
        dst_chain_name, wnft_contract, _, wormhole_id = MERKLY_WORMHOLE_INFO[MERKLY_WRAPPED_NETWORK[dst_chain]]

        estimate_fee = (await onft_contract.functions.quoteBridge(
            wormhole_id,
            0,
            200000
        ).call())[0]

        mint_price_in_wei = int(mint_price * 10 ** 18)

        self.logger_msg(
            *self.client.acc_info,
            msg=f"Mint NFT on Merkly Wormhole. Price for mint: {mint_price} {self.client.network.token}")

        transaction = await onft_contract.functions.mint(
            1
        ).build_transaction(await self.client.prepare_transaction(value=mint_price_in_wei))

        tx_hash = await self.client.send_transaction(transaction, need_hash=True)

        nft_id = await self.get_nft_id(tx_hash)

        await sleep(self, 5, 8)

        self.logger_msg(
            *self.client.acc_info,
            msg=f"Bridge NFT on Merkly Wormhole. Price for bridge: "
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
