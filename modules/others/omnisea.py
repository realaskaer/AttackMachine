import random
import time

from modules import Creator, Logger
from utils.tools import gas_checker, helper
from string import ascii_letters
from config import OMNISEA_ABI, OMNISEA_CONTRACT


class Omnisea(Creator, Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)
        self.network = self.client.network.name

    @helper
    @gas_checker
    async def create(self):
        self.logger_msg(*self.client.acc_info, msg=f"Create NFT collection on Omnisea")

        contract = self.client.get_contract(OMNISEA_CONTRACT[self.network]['drop_factory'], OMNISEA_ABI)

        tx_params = await self.client.prepare_transaction()

        name = "".join(random.sample(ascii_letters, random.randint(5, 15)))
        symbol = "".join(random.sample(ascii_letters, random.randint(3, 6)))
        ipsf = "".join(random.sample(ascii_letters, 20))
        uri = f'QmTuduie9dtu22GG8s{ipsf}ycPkcuCk'
        tokens_url = ""
        totap_supply = random.randrange(5000, 15000)
        is_edition = random.choice([True, False])
        is_sbt = random.choice([True, False])
        is_zero_indexed = random.choice([True, False])
        royalty_amount = random.randrange(1, 5)
        end_time = int(time.time()) + random.randrange(1000000, 2000000)

        self.logger_msg(*self.client.acc_info, msg=f"Create NFT collection on Omnisea | Name: {name} Symbol: {symbol}")

        transaction = await contract.functions.create([
            name,
            symbol,
            uri,
            tokens_url,
            totap_supply,
            is_zero_indexed,
            royalty_amount,
            end_time,
            is_edition,
            is_sbt,
            0
        ]).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)
