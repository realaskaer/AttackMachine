import random

from web3.exceptions import Web3ValidationError, ContractLogicError

from modules import Refuel, Logger
from modules.interfaces import BlockchainException, BlockchainExceptionWithoutRetry, SoftwareException
from settings import DST_CHAIN_L2PASS_REFUEL, DST_CHAIN_L2PASS_NFT, L2PASS_GAS_STATION_DATA
from eth_abi import encode
from utils.tools import gas_checker, helper, sleep
from config import (
    L2PASS_CONTRACTS_PER_CHAINS,
    L2PASS_ABI,
    LAYERZERO_NETWORKS_DATA, ZERO_ADDRESS, LAYERZERO_WRAPED_NETWORKS
)


class L2Pass(Refuel, Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)

    async def get_nft_id(self, contract):
        balance_nft = await contract.functions.balanceOf(self.client.address).call()
        nft_ids = []
        for i in range(balance_nft):
            nft_ids.append(await contract.functions.tokenOfOwnerByIndex(self.client.address, i).call())
        if nft_ids:
            return nft_ids[-1]
        return False

    async def get_estimate_send_fee(self, contract, adapter_params, dst_chain_id, nft_id):
        estimate_gas_bridge_fee = (await contract.functions.estimateSendFee(
            dst_chain_id,
            self.client.address,
            nft_id,
            False,
            adapter_params
        ).call())[0]

        return estimate_gas_bridge_fee

    @helper
    @gas_checker
    async def refuel(self, chain_from_id, attack_mode: bool = False, attack_data: dict = None, need_check:bool = False):
        if not attack_mode and attack_data is None:
            dst_data = random.choice(list(DST_CHAIN_L2PASS_REFUEL.items()))
        else:
            dst_data = random.choice(list(attack_data.items()))

        dst_chain_name, dst_chain_id, dst_native_name, dst_native_api_name = LAYERZERO_NETWORKS_DATA[dst_data[0]]
        dst_amount = self.client.round_amount(*dst_data[1])

        if not need_check:
            refuel_info = f'{dst_amount} {dst_native_name} to {dst_chain_name} from {self.client.network.name}'
            self.logger_msg(*self.client.acc_info, msg=f'Refuel on L2Pass: {refuel_info}')

        l2pass_contracts = L2PASS_CONTRACTS_PER_CHAINS[chain_from_id]
        refuel_contract = self.client.get_contract(l2pass_contracts['refuel'], L2PASS_ABI['refuel'])

        dst_native_gas_amount = int(dst_amount * 10 ** 18)
        dst_contract_address = L2PASS_CONTRACTS_PER_CHAINS[LAYERZERO_WRAPED_NETWORKS[dst_data[0]]]['refuel']

        try:
            estimate_send_fee = (await refuel_contract.functions.estimateGasRefuelFee(
                dst_chain_id,
                dst_native_gas_amount,
                dst_contract_address,
                False
            ).call())[0]

            transaction = await refuel_contract.functions.gasRefuel(
                dst_chain_id,
                ZERO_ADDRESS,
                dst_native_gas_amount,
                self.client.address
            ).build_transaction(await self.client.prepare_transaction(value=estimate_send_fee))

            if need_check:
                return True

            tx_hash = await self.client.send_transaction(transaction, need_hash=True)

            result = True
            if isinstance(tx_hash, bytes):
                if self.client.network.name != 'Polygon':
                    result = await self.client.wait_for_l0_received(tx_hash)
            elif isinstance(tx_hash, bool):
                result = tx_hash

            if attack_data and attack_mode is False:
                return LAYERZERO_WRAPED_NETWORKS[chain_from_id], dst_chain_id
            return result

        except Web3ValidationError as error:
            if not need_check:
                raise BlockchainExceptionWithoutRetry(f'{error}')

        except Exception as error:
            if not need_check:
                raise BlockchainException(f'{error}')

    @helper
    @gas_checker
    async def mint(self, chain_from_id):
        onft_contract = self.client.get_contract(L2PASS_CONTRACTS_PER_CHAINS[chain_from_id]['ONFT'], L2PASS_ABI['ONFT'])

        mint_price = await onft_contract.functions.mintPrice().call()

        self.logger_msg(
            *self.client.acc_info,
            msg=f"Mint L2Pass NFT on {self.client.network.name}. "
                f"Mint Price: {(mint_price / 10 ** 18):.5f} {self.client.network.token}")

        tx_params = await self.client.prepare_transaction(value=mint_price)

        transaction = await onft_contract.functions.mintWithReferral(
            1,
            '0x000000a679C2FB345dDEfbaE3c42beE92c0Fb7A5'
        ).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)

    @helper
    @gas_checker
    async def bridge(self, chain_from_id, attack_mode:bool = False, attack_data:int = None):
        if not attack_mode and attack_data is None:
            dst_chain = random.choice(DST_CHAIN_L2PASS_NFT)
        else:
            dst_chain = attack_data

        onft_contract = self.client.get_contract(L2PASS_CONTRACTS_PER_CHAINS[chain_from_id]['ONFT'], L2PASS_ABI['ONFT'])

        dst_chain_name, dst_chain_id, _, _ = LAYERZERO_NETWORKS_DATA[dst_chain]

        nft_id = await self.get_nft_id(onft_contract)

        if not nft_id:
            new_client = await self.client.new_client(chain_from_id)
            await L2Pass(new_client).mint(chain_from_id)
            nft_id = await self.get_nft_id(onft_contract)
            await sleep(self, 5, 10)

        self.logger_msg(
            *self.client.acc_info,
            msg=f"Bridge L2Pass NFT from {self.client.network.name} to {dst_chain_name}. ID: {nft_id}")

        version, gas_limit = 1, 200000

        adapter_params = encode(["uint16", "uint256"],
                                [version, gas_limit])

        adapter_params = self.client.w3.to_hex(adapter_params[30:])

        send_price = await onft_contract.functions.sendPrice().call()

        estimate_send_fee = await self.get_estimate_send_fee(onft_contract, adapter_params, dst_chain_id, nft_id)

        tx_params = await self.client.prepare_transaction(value=int(estimate_send_fee + send_price))

        transaction = await onft_contract.functions.sendFrom(
            self.client.address,
            dst_chain_id,
            self.client.address,
            nft_id,
            self.client.address,
            ZERO_ADDRESS,
            adapter_params
        ).build_transaction(tx_params)

        tx_hash = await self.client.send_transaction(transaction, need_hash=True)

        if attack_data and attack_mode is False:
            await self.client.wait_for_l0_received(tx_hash)
            return LAYERZERO_WRAPED_NETWORKS[chain_from_id], dst_chain_id

        return await self.client.wait_for_l0_received(tx_hash)

    @helper
    @gas_checker
    async def gas_station(self, chain_from_id):

        gas_data = L2PASS_GAS_STATION_DATA
        random.shuffle(gas_data)
        total_gas = 0
        refuel_list = []

        gas_contract = self.client.get_contract(
            L2PASS_CONTRACTS_PER_CHAINS[chain_from_id]['gas_station'], L2PASS_ABI['gas_station']
        )

        for refuel_data in gas_data:
            if isinstance(refuel_data, tuple):
                refuel_data = random.choice(refuel_data)
            if not refuel_data:
                continue
            chain_id_to, amount = refuel_data
            dst_chain_name, dst_chain_id, dst_native_name, dst_native_api_name = LAYERZERO_NETWORKS_DATA[chain_id_to]
            dst_amount = int(self.client.round_amount(*(amount, amount * 1.2)) * 10 ** 18)
            adapter_params = await gas_contract.functions.createAdapterParams(
                dst_chain_id,
                dst_amount,
                self.client.address
            ).call()

            gas_for_refuel = await gas_contract.functions.estimateFees(
                dst_chain_id,
                adapter_params
            ).call()

            refuel_list.append([dst_chain_id, dst_amount])
            total_gas += gas_for_refuel

        self.logger_msg(
            *self.client.acc_info,
            msg=f"Refuel with Gas Station from {self.client.network.name}. LayerZero transactions: {len(refuel_list)}")

        try:
            transaction = await gas_contract.functions.useGasStation(
                refuel_list,
                self.client.address
            ).build_transaction(await self.client.prepare_transaction(value=int(total_gas * 1.01)))

            tx_hash = await self.client.send_transaction(transaction, need_hash=True)

            if self.client.network.name != 'Polygon':
                return await self.client.wait_for_l0_received(tx_hash)
            return True if tx_hash else False
        except Exception as error:
            raise SoftwareException(f'Problem during the Gas Station: {error}')
