from config import ZERO_ADDRESS, COREDAO_CONTRACS, COREDAO_TOKENS_CONTRACS, COREDAO_ABI
from modules import Logger


class CoreDAO(Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)
        self.network = self.client.network.name

    async def bridge(self, swapdata:dict):

        src_chain_name, dst_chain_name, dst_chain_id, from_token_name, to_token_name, amount, amount_in_wei = swapdata

        self.logger_msg(
            *self.client.acc_info,
            msg=f'Bridge {amount} {from_token_name} {src_chain_name} to {to_token_name} {dst_chain_name}')

        token_address = COREDAO_TOKENS_CONTRACS[self.network][from_token_name]
        refund_address, zro_payment_address = self.client.address, ZERO_ADDRESS

        await self.client.check_for_approved(token_address, COREDAO_CONTRACS[self.network], amount_in_wei)

        if src_chain_name != 'CoreDAO':
            router_contract = self.client.get_contract(COREDAO_CONTRACS[self.network], COREDAO_ABI['router'])
            estimate_fee = (await router_contract.functions.estimateBridgeFee(
                False,
                "0x"
            ).call())[0]

            transaction = await router_contract.functions.bridge(
                token_address,
                amount_in_wei,
                self.client.address,
                [
                    refund_address,
                    zro_payment_address
                ],
                '0x'
            ).build_transaction(await self.client.prepare_transaction(value=estimate_fee))
        else:
            router_contract = self.client.get_contract(COREDAO_CONTRACS[self.network], COREDAO_ABI['core_router'])

            estimate_fee = (await router_contract.functions.estimateBridgeFee(
                dst_chain_id,
                False,
                "0x"
            ).call())[0]

            transaction = await router_contract.functions.bridge(
                token_address,
                dst_chain_id,
                amount_in_wei,
                self.client.address,
                False,
                [
                    refund_address,
                    zro_payment_address
                ],
                '0x'
            ).build_transaction(await self.client.prepare_transaction(value=estimate_fee))

        tx_hash = await self.client.send_transaction(transaction, need_hash=True)

        return await self.client.wait_for_l0_received(tx_hash)
