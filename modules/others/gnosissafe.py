from time import time
from modules import Creator
from utils.tools import gas_checker, repeater
from config import SAFE_ABI, SAFE_CONTRACTS, ZERO_ADDRESS


class GnosisSafe(Creator):
    @repeater
    @gas_checker
    async def create(self):
        self.client.logger.info(f'{self.client.info} Create safe on chain')

        safe_contract = self.client.get_contract(SAFE_CONTRACTS['proxy_factory'], SAFE_ABI)
        tx_params = await self.client.prepare_transaction()
        deadline = int(time()) + 1800

        setup_data = safe_contract.encodeABI(
            fn_name="setup",
            args=[
                [self.client.address],
                1,
                ZERO_ADDRESS,
                "0x",
                SAFE_CONTRACTS['fallback_handler'],
                ZERO_ADDRESS,
                0,
                ZERO_ADDRESS
            ]
        )

        transaction = await safe_contract.functions.createProxyWithNonce(
            SAFE_CONTRACTS['gnosis_safe'],
            setup_data,
            deadline
        ).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)
