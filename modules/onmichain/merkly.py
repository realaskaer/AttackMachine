import random

from modules import Refuel, Logger
from eth_abi import abi
from settings import DST_CHAIN_MERKLY_REFUEL
from utils.tools import gas_checker, helper
from config import (
    MERKLY_CONTRACTS_PER_CHAINS,
    MERKLY_ABI,
    LAYERZERO_NETWORKS_DATA, CHAIN_NAME
)


class Merkly(Refuel, Logger):
    def __init__(self, client):
        super().__init__()
        self.client = client

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
        #endpoint_contract = self.client.get_contract(merkly_contracts['endpoint'], MERKLY_ABI['endpoint'])

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

        # estimate_bridge_fee = (await endpoint_contract.functions.estimateFees(
        #     dst_chain_id,
        #     dst_contract_address,
        #     "0x",
        #     False,
        #     adapter_params
        # ).call())[0]

        value = estimate_send_fee  # + estimate_bridge_fee

        tx_params = await self.client.prepare_transaction(value=value)

        transaction = await refuel_contract.functions.bridgeGas(
            dst_chain_id,
            self.client.address,
            adapter_params
        ).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)
