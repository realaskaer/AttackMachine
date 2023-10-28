import random

from modules import Client
from eth_abi import abi
from settings import DESTINATION_MERKLY_DATA
from utils.tools import gas_checker, repeater
from config import (
    MERKLY_CONTRACTS,
    MERKLY_ROUTER_ABI,
    LAYERZERO_NETWORKS_DATA
)


class Merkly(Client):
    def __init__(self, account_number, private_key, network, proxy=None):
        super().__init__(account_number, private_key, network, proxy)
        self.refuel_contract = self.get_contract(MERKLY_CONTRACTS['gas_refuel'], MERKLY_ROUTER_ABI)
        self.router_contract = self.get_contract(MERKLY_CONTRACTS['router'], MERKLY_ROUTER_ABI)

    @repeater
    @gas_checker
    async def refuel(self):

        dst_data = random.choice(list(DESTINATION_MERKLY_DATA.items()))
        dst_chain_name, dst_chain_id, dst_native_name, dst_native_api_name = LAYERZERO_NETWORKS_DATA[dst_data[0]]
        dst_amount = self.round_amount(*dst_data[1])

        refuel_info = f'{dst_amount} {dst_native_name} to {dst_chain_name.capitalize()}'
        self.logger.info(f'{self.info} Refuel on Merkly: {refuel_info}')

        dst_native_gas_amount = int(dst_amount * 10 ** 18)

        gas_limit = 200000

        adapter_params = abi.encode(["uint16", "uint64", "uint256"],
                                    [2, gas_limit, dst_native_gas_amount])

        adapter_params = self.w3.to_hex(adapter_params[30:]) + self.address[2:].lower()

        estimate_gas_bridge_fee = (await self.router_contract.functions.estimateGasBridgeFee(
            dst_chain_id,
            False,
            adapter_params
        ).call())[0]

        value = (int(dst_native_gas_amount * (await self.get_token_price(dst_native_api_name, 'eth')))
                 + estimate_gas_bridge_fee)

        tx_params = await self.prepare_transaction(value=value)

        transaction = await self.refuel_contract.functions.bridgeGas(
            dst_chain_id,
            self.address,
            adapter_params
        ).build_transaction(tx_params)

        tx_hash = await self.send_transaction(transaction)

        await self.verify_transaction(tx_hash)
