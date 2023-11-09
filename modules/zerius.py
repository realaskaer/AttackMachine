import random

from settings import DESTINATION_ZERIUS
from config import ZERIUS_CONTRACT_PER_CHAINS, ZERIUS_ABI, ZERO_ADDRESS, LAYERZERO_NETWORKS_DATA
from utils.tools import gas_checker, repeater, sleep
from eth_abi import encode
from modules import Minter


class Zerius(Minter):
    def __init__(self, client, chain_from_id):
        self.client = client

        self.contract = self.client.get_contract(ZERIUS_CONTRACT_PER_CHAINS[chain_from_id]['ONFT'], ZERIUS_ABI)

    async def get_nft_id(self):
        balance_nft = self.contract.functions.balanceOf(self.client.address).call()
        nft_ids = []
        for i in range(balance_nft):
            nft_ids.append(self.contract.tokenOfOwnerByIndex(self.client.address, i).call())
        return nft_ids[-1]

    async def get_estimate_gas_bridge_fee(self, adapter_params, dst_chain_id, nft_id):

        estimate_gas_bridge_fee = (await self.contract.functions.estimateGasBridgeFee(
            dst_chain_id,
            self.client.address,
            nft_id,
            False,
            adapter_params
        ).call())[0]

        return estimate_gas_bridge_fee

    @repeater
    @gas_checker
    async def mint(self):

        mint_price = await self.contract.functions.mintFee().call()

        self.client.logger.info(f"{self.client.info} Zerius | Mint Zerius NFT. Price: {(mint_price / 10 ** 18):.5f}")

        tx_params = await self.client.get_tx_data(mint_price)

        transaction = await self.contract.functions.mint().build_transaction(tx_params)

        tx_hash = await self.client.send_transaction(transaction)

        await self.client.verify_transaction(tx_hash)

        return tx_hash

    @repeater
    @gas_checker
    async def bridge(self):

        dst_chain = random.choice(DESTINATION_ZERIUS)
        dst_chain_name, dst_chain_id, _, _ = LAYERZERO_NETWORKS_DATA[dst_chain]

        nft_id = await self.get_nft_id()

        if not nft_id:
            await self.mint()

        self.client.logger.info(f"{self.client.info} Zerius | Bridge Zerius NFT to {dst_chain_name}. ID: {nft_id}")

        await sleep(5, 10)

        version, gas_limit = 1, await self.contract.functions.minDstGasLookup(dst_chain_id, 1).call()

        adapter_params = encode(["uint16", "uint256"],
                                [version, gas_limit])

        adapter_params = self.client.w3.to_hex(adapter_params[30:]) + self.client.address[2:].lower()

        base_bridge_fee = await self.contract.functions.bridgeFee().call()
        estimate_gas_bridge_fee = await self.get_estimate_gas_bridge_fee(adapter_params, dst_chain_id, nft_id)

        tx_params = await self.client.prepare_transaction(value=estimate_gas_bridge_fee + base_bridge_fee)

        transaction = await self.contract.functions.sendFrom(
            self.client.address,
            dst_chain_id,
            self.client.address,
            nft_id,
            ZERO_ADDRESS,
            ZERO_ADDRESS,
            adapter_params
        ).build_transaction(tx_params)

        tx_hash = await self.client.send_transaction(transaction)

        await self.client.verify_transaction(tx_hash)
