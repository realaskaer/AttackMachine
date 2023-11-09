import random

from modules import Refuel
from eth_abi import abi
from settings import DESTINATION_MERKLY_DATA
from utils.tools import gas_checker, repeater
from config import (
    MERKLY_CONTRACTS_PER_CHAINS,
    MERKLY_ROUTER_ABI,
    LAYERZERO_NETWORKS_DATA
)


class Merkly(Refuel):
    def __init__(self, client):
        self.client = client

    @repeater
    @gas_checker
    async def refuel(self, chain_from_id):

        dst_data = random.choice(list(DESTINATION_MERKLY_DATA.items()))
        dst_chain_name, dst_chain_id, dst_native_name, dst_native_api_name = LAYERZERO_NETWORKS_DATA[dst_data[0]]
        dst_amount = self.client.round_amount(*dst_data[1])

        merkly_contracts = MERKLY_CONTRACTS_PER_CHAINS[chain_from_id]

        refuel_contract = self.client.get_contract(merkly_contracts['gas_refuel'], MERKLY_ROUTER_ABI)
        router_contract = self.client.get_contract(merkly_contracts['ONFT'], MERKLY_ROUTER_ABI)

        refuel_info = f'{dst_amount} {dst_native_name} to {dst_chain_name}'
        self.client.logger.info(f'{self.client.info} Merkly | Refuel on Merkly: {refuel_info}')

        dst_native_gas_amount = int(dst_amount * 10 ** 18)

        gas_limit = 200000

        adapter_params = abi.encode(["uint16", "uint64", "uint256"],
                                    [2, gas_limit, dst_native_gas_amount])

        adapter_params = self.client.w3.to_hex(adapter_params[30:]) + self.client.address[2:].lower()

        estimate_gas_bridge_fee = (await router_contract.functions.estimateGasBridgeFee(
            dst_chain_id,
            False,
            adapter_params
        ).call())[0]

        value = (int(dst_native_gas_amount * (await self.client.get_token_price(dst_native_api_name, 'eth')))
                 + estimate_gas_bridge_fee)

        tx_params = await self.client.prepare_transaction(value=value)

        transaction = await refuel_contract.functions.bridgeGas(
            dst_chain_id,
            self.client.address,
            adapter_params
        ).build_transaction(tx_params)

        tx_hash = await self.client.send_transaction(transaction)

        await self.client.verify_transaction(tx_hash)
