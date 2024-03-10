import random

from modules.interfaces import BlockchainException, SoftwareException, Refuel
from utils.tools import sleep, helper
from eth_abi import encode
from modules import Minter, Logger, Client
from config import (ZERIUS_CONTRACT_PER_CHAINS, ZERIUS_ABI, ZERO_ADDRESS, LAYERZERO_NETWORKS_DATA,
                    LAYERZERO_WRAPED_NETWORKS)


class Zerius(Refuel, Minter, Logger):
    def __init__(self, client: Client):
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

    async def get_estimate_send_fee(self, contract,  adapter_params, dst_chain_id, nft_id):
        estimate_send_fee = (await contract.functions.estimateSendFee(
            dst_chain_id,
            self.client.address,
            nft_id,
            False,
            adapter_params
        ).call())[0]

        return estimate_send_fee

    @helper
    async def refuel(
            self, chain_from_id: int, attack_data: dict, google_mode: bool = False, need_check: bool = False
    ):
        dst_data = random.choice(list(attack_data.items()))
        dst_chain_name, dst_chain_id, dst_native_name, dst_native_api_name = LAYERZERO_NETWORKS_DATA[dst_data[0]]
        dst_amount = await self.client.get_smart_amount(dst_data[1])

        if not need_check:
            refuel_info = f'{dst_amount} {dst_native_name} to {dst_chain_name} from {self.client.network.name}'
            self.logger_msg(*self.client.acc_info, msg=f'Refuel on Zerius: {refuel_info}')

        l2pass_contracts = ZERIUS_CONTRACT_PER_CHAINS[chain_from_id]
        refuel_contract = self.client.get_contract(l2pass_contracts['refuel'], ZERIUS_ABI['refuel'])

        dst_native_gas_amount = int(dst_amount * 10 ** 18)
        dst_contract_address = ZERIUS_CONTRACT_PER_CHAINS[LAYERZERO_WRAPED_NETWORKS[dst_data[0]]]['refuel']

        gas_limit = await refuel_contract.functions.minDstGasLookup(dst_chain_id, 0).call()

        if gas_limit == 0 and not need_check:
            raise SoftwareException('This refuel path is not active!')

        adapter_params = encode(["uint16", "uint64", "uint256"],
                                [2, gas_limit, dst_native_gas_amount])

        adapter_params = self.client.w3.to_hex(adapter_params[30:]) + self.client.address[2:].lower()

        try:
            estimate_send_fee = (await refuel_contract.functions.estimateSendFee(
                dst_chain_id,
                dst_contract_address,
                adapter_params
            ).call())[0]

            tx_params = await self.client.prepare_transaction(value=estimate_send_fee)

            transaction = await refuel_contract.functions.refuel(
                dst_chain_id,
                dst_contract_address,
                adapter_params
            ).build_transaction(tx_params)

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

    async def mint(self, chain_from_id):
        onft_contract = self.client.get_contract(ZERIUS_CONTRACT_PER_CHAINS[chain_from_id]['ONFT'], ZERIUS_ABI['ONFT'])

        mint_price = await onft_contract.functions.mintFee().call()

        self.logger_msg(
            *self.client.acc_info, msg=f"Mint Zerius NFT on {self.client.network.name}. "
                                       f"Mint Price: {(mint_price / 10 ** 18):.5f} {self.client.network.token}")

        tx_params = await self.client.prepare_transaction(value=mint_price)

        transaction = await onft_contract.functions.mint(
            '0x000000a679C2FB345dDEfbaE3c42beE92c0Fb7A5'
        ).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)

    @helper
    async def bridge(
            self, chain_from_id: int, attack_data: int, google_mode: bool = False, need_check: bool = False
    ):
        dst_chain = attack_data
        onft_contract = self.client.get_contract(ZERIUS_CONTRACT_PER_CHAINS[chain_from_id]['ONFT'], ZERIUS_ABI['ONFT'])

        dst_chain_name, dst_chain_id, _, _ = LAYERZERO_NETWORKS_DATA[dst_chain]

        if not need_check:
            nft_id = await self.get_nft_id(onft_contract)

            if not nft_id:
                await self.mint(chain_from_id)
                nft_id = await self.get_nft_id(onft_contract)
                await sleep(self, 5, 10)

            self.logger_msg(
                *self.client.acc_info,
                msg=f"Bridge Zerius NFT from {self.client.network.name} to {dst_chain_name}. ID: {nft_id}")
        else:
            nft_id = await onft_contract.functions.startMintId().call()

        try:
            version, gas_limit = 1, await onft_contract.functions.minDstGasLookup(dst_chain_id, 1).call()

            adapter_params = encode(["uint16", "uint256"],
                                    [version, gas_limit])

            adapter_params = self.client.w3.to_hex(adapter_params[30:])

            base_bridge_fee = await onft_contract.functions.bridgeFee().call()
            estimate_send_fee = await self.get_estimate_send_fee(onft_contract, adapter_params, dst_chain_id, nft_id)
            value = int(estimate_send_fee + base_bridge_fee)

            if need_check:
                if await self.client.w3.eth.get_balance(self.client.address) > value:
                    return True
                return False

            tx_params = await self.client.prepare_transaction(value=value)

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
