from config import STARGATE_ABI, STARGATE_CONTRACTS, STARGATE_POOLS_ID
from modules import Logger


class Stargate(Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)
        self.network = self.client.network.name

    async def bridge(self, swapdata:dict):

        src_chain_name, dst_chain_id, dst_chain_name, from_token_name, to_token_name, amount, amount_in_wei = swapdata

        self.logger_msg(
            *self.client.acc_info,
            msg=f'Bridge {amount} {from_token_name} {src_chain_name} to {to_token_name} {dst_chain_name} on Stargate')

        contracts = STARGATE_CONTRACTS[self.network]

        router_contract = self.client.get_contract(contracts['router'], STARGATE_ABI['router'])
        # bridge_contract = self.client.get_contract(contracts['bridge'], STARGATE_ABI['bridge'])
        # factory_contract = self.client.get_contract(contracts['factory'], STARGATE_ABI['factory'])

        scr_pool_id = STARGATE_POOLS_ID[self.network][from_token_name]
        dst_pool_id = STARGATE_POOLS_ID[dst_chain_name][to_token_name]
        dst_gas_for_call, dst_native_amount, dst_native_addr = 0, 0, '0x0000000000000000000000000000000000000001'
        function_type = 1
        min_amount_out = int(amount_in_wei * 0.995)

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
