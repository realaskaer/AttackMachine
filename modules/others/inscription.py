from modules import Logger
from settings import INSCRIPTION_DATA
from utils.tools import helper


class Inscription(Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)

    @helper
    async def mint_inscribe(self):
        tx_params = (await self.client.prepare_transaction()) | {
            'data': (f"0x{INSCRIPTION_DATA.encode().hex()}"
                     if isinstance(INSCRIPTION_DATA, str) else f"{INSCRIPTION_DATA}"),
            'to': self.client.address
        }

        return await self.client.send_transaction(tx_params)
