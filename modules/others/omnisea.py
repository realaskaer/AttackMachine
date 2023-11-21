import random
import time

from modules import Creator
from utils.tools import gas_checker, repeater
from string import ascii_letters
from config import OMNISEA_ABI, OMNISEA_CONTRACT


class Omnisea(Creator):
    @repeater
    @gas_checker
    async def create(self):
        self.client.logger.info(f"{self.client.info} Create NFT collection on Omnisea")

        contract = self.client.get_contract(OMNISEA_CONTRACT['drop_factory'], OMNISEA_ABI)

        tx_params = await self.client.prepare_transaction()

        name = "".join(random.sample(ascii_letters, random.randint(5, 15)))
        symbol = "".join(random.sample(ascii_letters, random.randint(3, 6)))
        ipsf = "".join(random.sample(ascii_letters, 20))
        uri = f'QmTuduie9dtu22GG8s{ipsf}ycPkcuCk'
        tokens_url = ""
        totap_supply = random.randrange(5000, 15000)
        is_zero_indexed = random.choice([True, False])
        royalty_amount = random.randrange(1, 5)
        end_time = int(time.time()) + random.randrange(1000000, 2000000)

        self.client.logger.info(f"{self.client.info} Create NFT collection on Omnisea | Name: {name} Symbol: {symbol}")

        transaction = await contract.functions.create([
            name,
            symbol,
            uri,
            tokens_url,
            totap_supply,
            is_zero_indexed,
            royalty_amount,
            end_time
        ]).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)
