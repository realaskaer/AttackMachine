from utils.tools import sleep, gas_checker, repeater
from modules import Minter, Logger
from config import (
    TEVAERA_CONTRACTS,
    TEVAERA_ABI,
)


class Tevaera(Minter, Logger):
    def __init__(self, client):
        super().__init__()
        self.client = client

        self.id_contract = self.client.get_contract(TEVAERA_CONTRACTS['citizen_id'], TEVAERA_ABI)
        self.nft_contract = self.client.get_contract(TEVAERA_CONTRACTS['nft_contract'], TEVAERA_ABI)

    @repeater
    async def mint_id(self):
        self.logger_msg(*self.client.acc_info, msg=f'Mint Tevaera Citizen ID')

        tx_params = await self.client.prepare_transaction(value=300000000000000)

        transaction = await self.id_contract.functions.mintCitizenId().build_transaction(tx_params)

        return await self.client.send_transaction(transaction)

    @repeater
    async def mint_nft(self):
        self.logger_msg(*self.client.acc_info, msg=f'Mint Tevaera Guardian NFT')

        tx_params = await self.client.prepare_transaction()

        transaction = await self.nft_contract.functions.mint().build_transaction(tx_params)

        return await self.client.send_transaction(transaction)

    # def mint_karma(self):
    #
    #     logger.info(f"{self.info} Add Karma on Tevaera")
    #
    #     karma_contract = self.get_contract(TEVAERA_KARMA_CONTRACT, TEVAERA_ABI)
    #
    #     karma_coins_amount = random.randrange(1, 4)
    #
    #     value = int(12000000000000 * karma_coins_amount)
    #
    #     tx_params = self.prepare_transaction()
    #
    #     transaction = karma_contract.functions.buy(
    #         karma_coins_amount
    #     ).build_transaction(tx_params)
    #
    #     tx_hash = self.send_transaction(transaction)
    #
    #     self.verify_transaction(tx_hash)

    @gas_checker
    async def mint(self):

        await self.mint_id()

        await sleep(self, 5, 10)

        await self.mint_nft()
