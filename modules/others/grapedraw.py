from config import GRAPEDRAW_CONTRACTS, GRAPEDRAW_ABI
from settings import GRAPEDRAW_TICKETS_AMOUNT
from utils.tools import helper, gas_checker
from modules import Logger


class GrapeDraw(Logger):
    def __init__(self, client):
        Logger.__init__(self)
        self.client = client

    @helper
    @gas_checker
    async def bid_place(self):

        bid_contract = self.client.get_contract(GRAPEDRAW_CONTRACTS[self.client.network.name], GRAPEDRAW_ABI)

        bid_price = int((await bid_contract.functions.bidPrice().call()) * GRAPEDRAW_TICKETS_AMOUNT)

        self.logger_msg(
            *self.client.acc_info, msg=f"Create bid on GrapeDraw. Price: {bid_price / 10 ** 18:.4f} ETH")

        transaction = await bid_contract.functions.Bid(
            GRAPEDRAW_TICKETS_AMOUNT
        ).build_transaction(await self.client.prepare_transaction(value=bid_price))

        return await self.client.send_transaction(transaction)
