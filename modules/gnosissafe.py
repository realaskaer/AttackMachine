from time import time
from modules import Client
from utils.tools import gas_checker, repeater
from config import SAFE_ABI, SAFE_CONTRACTS, ZERO_ADDRESS


class GnosisSafe(Client):

    @repeater
    @gas_checker
    async def create_safe(self):
        self.logger.info(f'{self.info} Create safe on chain')

        safe_contract = self.get_contract(SAFE_CONTRACTS['proxy_factory'], SAFE_ABI)
        tx_params = await self.prepare_transaction()
        deadline = int(time()) + 1800

        setup_data = safe_contract.encodeABI(
            fn_name="setup",
            args=[
                [self.address],
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

        tx_hash = await self.send_transaction(transaction)

        await self.verify_transaction(tx_hash)
