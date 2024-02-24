import time

from eth_abi import abi

from config import STARGATE_ABI, STARGATE_CONTRACTS, STARGATE_POOLS_ID, TOKENS_PER_CHAIN2, USDV_ABI, ZERO_ADDRESS, \
    STG_ABI, L0_ENDPOINT_ABI, STARGATE_STG_CONFIG_CHECKERS, VESTG_ADDRESS, VESTG_ABI
from modules import Logger, Client
from utils.tools import helper, gas_checker


class Stargate(Logger):
    def __init__(self, client: Client):
        self.client = client
        Logger.__init__(self)
        self.network = self.client.network.name
        # factory_contract = self.client.get_contract(contracts['factory'], STARGATE_ABI['factory'])

    @helper
    @gas_checker
    async def bridge(self, swapdata:dict):

        src_chain_name, dst_chain_name, dst_chain_id, from_token_name, to_token_name, amount, amount_in_wei = swapdata

        self.logger_msg(
            *self.client.acc_info,
            msg=f'Bridge {amount} {from_token_name} from {src_chain_name} to {to_token_name} {dst_chain_name}')

        contracts = STARGATE_CONTRACTS[self.network]
        min_amount_out = int(amount_in_wei * 0.995)
        dst_gas_for_call, dst_native_amount, dst_native_addr = 0, 0, '0x0000000000000000000000000000000000000001'

        if from_token_name == 'STG':
            stg_contract = self.client.get_contract(TOKENS_PER_CHAIN2[self.network]['STG'], STG_ABI)
            config_checker = self.client.get_contract(
                STARGATE_STG_CONFIG_CHECKERS[self.network], STARGATE_ABI['configer'])

            _, base_gas, _ = await config_checker.functions.dstConfigLookup(
                dst_chain_id,
                1
            ).call()

            endpoint_address = await stg_contract.functions.endpoint().call()
            endpoint_contract = self.client.get_contract(endpoint_address, L0_ENDPOINT_ABI)

            adapter_params = abi.encode(["uint16", "uint64"], [1, base_gas])
            adapter_params = self.client.w3.to_hex(adapter_params[30:])

            estimate_fee = (await endpoint_contract.functions.estimateFees(
                dst_chain_id,
                self.client.address,
                adapter_params,
                False,
                "0x"
            ).call())[0]

            transaction = await stg_contract.functions.sendTokens(
                dst_chain_id,
                self.client.address,
                amount_in_wei,
                ZERO_ADDRESS,
                adapter_params
            ).build_transaction(await self.client.prepare_transaction(value=int(estimate_fee * 1.05)))

        elif from_token_name == 'USDV':
            router_contract = self.client.get_contract(TOKENS_PER_CHAIN2[self.network]['USDV'], USDV_ABI)
            msg_contract_address = await router_contract.functions.getRole(3).call()
            msg_contract = self.client.get_contract(msg_contract_address, STARGATE_ABI['messagingV1'])

            min_gas_limit = await msg_contract.functions.minDstGasLookup(
                dst_chain_id,
                1
            ).call()

            encode_address = abi.encode(["address"], [self.client.address])
            adapter_params = abi.encode(["uint16", "uint64"], [1, min_gas_limit])
            adapter_params = self.client.w3.to_hex(adapter_params[30:])

            estimate_fee = (await router_contract.functions.quoteSendFee(
                [
                    encode_address,
                    amount_in_wei,
                    min_amount_out,
                    dst_chain_id
                ],
                adapter_params,
                False,
                "0x"
            ).call())[0]

            transaction = await router_contract.functions.send(
                [
                    encode_address,
                    amount_in_wei,
                    min_amount_out,
                    dst_chain_id
                ],
                adapter_params,
                [
                    dst_gas_for_call,
                    dst_native_amount,
                ],
                self.client.address,
                '0x'
            ).build_transaction(await self.client.prepare_transaction(value=estimate_fee))
        else:
            router_contract = self.client.get_contract(contracts['router'], STARGATE_ABI['router'])
            scr_pool_id = STARGATE_POOLS_ID[self.network][from_token_name]
            dst_pool_id = STARGATE_POOLS_ID[dst_chain_name][to_token_name]
            token_address = TOKENS_PER_CHAIN2[self.network][from_token_name]
            function_type = 1

            estimate_fee = (await router_contract.functions.quoteLayerZeroFee(
                dst_chain_id,
                function_type,
                STARGATE_CONTRACTS[dst_chain_name][to_token_name],
                "0x",
                (
                    dst_gas_for_call,
                    dst_native_amount,
                    dst_native_addr
                )
            ).call())[0]

            if from_token_name == 'ETH':
                router_eth_contract = self.client.get_contract(contracts['router_eth'], STARGATE_ABI['router_eth'])
                transaction = await router_eth_contract.functions.swapETH(
                    dst_chain_id,
                    self.client.address,
                    self.client.address,
                    amount_in_wei,
                    min_amount_out
                ).build_transaction(await self.client.prepare_transaction(value=estimate_fee + amount_in_wei))
            else:
                await self.client.check_for_approved(token_address, contracts['router'], amount_in_wei)

                transaction = await router_contract.functions.swap(
                    dst_chain_id,
                    scr_pool_id,
                    dst_pool_id,
                    self.client.address,
                    amount_in_wei,
                    min_amount_out,
                    [
                        dst_gas_for_call,
                        dst_native_amount,
                        dst_native_addr,
                    ],
                    self.client.address,
                    '0x'
                ).build_transaction(await self.client.prepare_transaction(value=estimate_fee))

        tx_hash = await self.client.send_transaction(transaction, need_hash=True)

        return await self.client.wait_for_l0_received(tx_hash)

    @helper
    async def stake_stg(self, stakedata:tuple):
        stake_amount, stake_amount_in_wei, lock_time = stakedata

        self.logger_msg(
            *self.client.acc_info, msg=f'Stake {stake_amount} STG on {self.client.network.name} for {lock_time} days')

        stg_contract_address = TOKENS_PER_CHAIN2[self.network]['STG']
        vestg_contract_address = VESTG_ADDRESS[self.network]
        vestg_contract = self.client.get_contract(vestg_contract_address, VESTG_ABI)
        deadline = int(int(time.time()) + (lock_time * 24 * 60 * 60))

        await self.client.check_for_approved(stg_contract_address, vestg_contract_address, stake_amount_in_wei)

        transaction = await vestg_contract.functions.create_lock(
            stake_amount_in_wei,
            deadline
        ).build_transaction(await self.client.prepare_transaction())

        return await self.client.send_transaction(transaction)
