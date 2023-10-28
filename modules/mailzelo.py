from utils.tools import gas_checker, repeater
from config import MAILZERO_ABI, MAILZERO_CONTRACT
from modules import Client


class MailZero(Client):

    @repeater
    @gas_checker
    async def mint(self, code_nft: int = 1):
        self.logger.info(f"{self.info} Mint free NFT on MailZero")

        mail_contract = self.get_contract(MAILZERO_CONTRACT['mail_contract'], MAILZERO_ABI)

        tx_params = await self.prepare_transaction()

        transaction = await mail_contract.functions.mint(code_nft).build_transaction(tx_params)

        tx_hash = await self.send_transaction(transaction)

        await self.verify_transaction(tx_hash)
