import random
from modules import Minter
from settings import USE_PROXY
from utils.tools import repeater, gas_checker
from config import STARKNET_ID_CONTRACT


class StarknetId(Minter):
    def __init__(self, client):
        self.client = client

    @repeater
    @gas_checker
    async def mint(self):
        try:
            await self.client.initialize_account()

            self.client.logger.info(f'{self.client.info} Mint identity on Starknet ID')

            domain_contract = STARKNET_ID_CONTRACT['register']

            identity = random.randint(10 ** 11, 10 ** 12 - 1)

            self.client.logger.info(f'{self.client.info} Generated identity: {identity}')

            mint_id_call = self.client.prepare_call(
                contract_address=domain_contract,
                selector_name="mint",
                calldata=[identity]
            )

            await self.client.send_transaction(mint_id_call)
        finally:
            if USE_PROXY:
                await self.client.session.close()
