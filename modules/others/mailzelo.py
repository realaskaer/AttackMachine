from utils.tools import gas_checker, helper
from config import MAILZERO_ABI, MAILZERO_CONTRACT
from modules import Minter, Logger


class MailZero(Minter, Logger):
    def __init__(self, client):
        super().__init__()
        self.client = client

    @helper
    @gas_checker
    async def mint(self, code_nft: int = 1):
        self.logger_msg(*self.client.acc_info, msg=f"Mint free NFT on MailZero")

        mail_contract = self.client.get_contract(MAILZERO_CONTRACT['mail_contract'], MAILZERO_ABI)

        tx_params = await self.client.prepare_transaction()

        transaction = await mail_contract.functions.mint(code_nft).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)
