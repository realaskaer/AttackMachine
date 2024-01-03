import random
from modules import Minter, Logger
from utils.tools import helper, gas_checker
from config import STARKNET_ID_CONTRACT


class StarknetId(Minter, Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)

    @helper
    @gas_checker
    async def mint(self):
        await self.client.initialize_account()

        self.logger_msg(*self.client.acc_info, msg=f'Mint identity on Starknet ID')

        domain_contract = STARKNET_ID_CONTRACT['register']

        identity = random.randint(10 ** 11, 10 ** 12 - 1)

        self.logger_msg(*self.client.acc_info, msg=f'Generated identity: {identity}')

        mint_id_call = self.client.prepare_call(
            contract_address=domain_contract,
            selector_name="mint",
            calldata=[identity]
        )

        await self.client.send_transaction(mint_id_call)
