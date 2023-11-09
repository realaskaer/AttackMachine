from utils.tools import gas_checker, repeater
from config import MAILZERO_ABI, MAILZERO_CONTRACT
from modules import Minter


class MailZero(Minter):
    def __init__(self, client):
        self.client = client

    @repeater
    @gas_checker
    async def mint(self, code_nft: int = 1):
        self.client.logger.info(f"{self.client.info} MailZero | Mint free NFT on MailZero")

        mail_contract = self.client.get_contract(MAILZERO_CONTRACT['mail_contract'], MAILZERO_ABI)

        tx_params = await self.client.prepare_transaction()

        transaction = await mail_contract.functions.mint(code_nft).build_transaction(tx_params)

        tx_hash = await self.client.send_transaction(transaction)

        await self.client.verify_transaction(tx_hash)
