from config import RUBYSCORE_CONTRACTS, RUBYSCORE_ABI
from utils.tools import helper, gas_checker
from modules import Logger


class RubyScore(Logger):
    def __init__(self, client):
        Logger.__init__(self)
        self.client = client

    @helper
    @gas_checker
    async def vote(self):

        vote_contract = self.client.get_contract(
            RUBYSCORE_CONTRACTS[self.client.network.name]['vote_contract'], RUBYSCORE_ABI
        )

        self.logger_msg(
            *self.client.acc_info, msg=f"Creating a vote on RubyScore")

        transaction = await vote_contract.functions.vote().build_transaction(await self.client.prepare_transaction())

        return await self.client.send_transaction(transaction)
