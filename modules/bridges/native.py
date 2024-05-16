from config import CHAIN_NAME_FROM_ID, ZERO_ADDRESS
from modules import Bridge, Logger
from modules.interfaces import SoftwareException, SoftwareExceptionWithoutRetry
from settings import WAIT_FOR_RECEIPT_BRIDGE


class NativeBridge(Bridge, Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)
        Bridge.__init__(self, client)

    @staticmethod
    async def get_bridge_class(from_chain_id, to_chain_id):
        from functions import ZkSync, Scroll, PolygonZkEVM, Linea, Base, Zora

        class_info = {
            8453: Base,
            59144: Linea,
            534352: Scroll,
            1101: PolygonZkEVM,
            324: ZkSync,
            7777777: Zora,
        }

        needed_chain_id = to_chain_id if from_chain_id == 1 else from_chain_id

        return class_info[needed_chain_id]

    async def bridge(self, chain_from_id: int, bridge_data: tuple, need_check: bool = False):
        from_chain, to_chain, amount, to_chain_id, from_token_name, to_token_name, from_token_address, to_token_address = bridge_data

        if need_check:
            return 0

        bridge_class = await self.get_bridge_class(from_chain, to_chain)

        old_balance_on_dst = await self.client.wait_for_receiving(
            token_address=to_token_address, token_name=to_token_name, chain_id=to_chain_id,
            check_balance_on_dst=True
        )

        if from_chain == 1:
            await bridge_class(self.client).deposit(amount)
        elif to_chain == 7777777 or from_chain == 7777777:
            await bridge_class(self.client).bridge(amount)
        else:
            await bridge_class(self.client).withdraw(amount)

        self.logger_msg(
            *self.client.acc_info, msg=f"Bridge complete. Note: wait a little for receiving funds",
            type_msg='success'
        )

        if WAIT_FOR_RECEIPT_BRIDGE:
            return await self.client.wait_for_receiving(
                token_address=to_token_address, token_name=to_token_name, old_balance=old_balance_on_dst,
                chain_id=to_chain_id
            )
        return True
