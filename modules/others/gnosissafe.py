from time import time
from modules import Creator, Logger
from utils.tools import gas_checker, helper
from config import SAFE_ABI, SAFE_CONTRACTS, ZERO_ADDRESS


class GnosisSafe(Creator, Logger):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.network = self.client.network.name

    @helper
    @gas_checker
    async def create(self):
        self.logger_msg(*self.client.acc_info, msg=f'Create safe on chain')

        safe_contract = self.client.get_contract(SAFE_CONTRACTS[self.network]['proxy_factory'], SAFE_ABI)
        tx_params = await self.client.prepare_transaction()
        deadline = int(time()) + 1800

        setup_data = safe_contract.encodeABI(
            fn_name="setup",
            args=[
                [self.client.address],
                1,
                ZERO_ADDRESS,
                "0x",
                SAFE_CONTRACTS[self.network]['fallback_handler'],
                ZERO_ADDRESS,
                0,
                ZERO_ADDRESS
            ]
        )

        transaction = await safe_contract.functions.createProxyWithNonce(
            SAFE_CONTRACTS[self.network]['gnosis_safe'],
            setup_data,
            deadline
        ).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)
