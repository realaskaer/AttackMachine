import random

from modules import Minter, Logger
from config import MINTFUN_ABI
from utils.tools import helper, gas_checker
from settings import MINTFUN_CONTRACTS


class MintFun(Minter, Logger):
    def __init__(self, client):
        super().__init__()
        self.client = client

    @helper
    @gas_checker
    async def mint(self, nft_contracts_data: dict):

        nft_contract, mint_price = random.choice(list(MINTFUN_CONTRACTS.items()))

        contract = self.client.get_contract(nft_contract, MINTFUN_ABI[1])

        try:
            nft_name = await contract.functions.name().call()
        except:
            nft_name = 'Random'

        self.logger_msg(*self.client.acc_info, msg=f"Mint {nft_name} NFT. Price: {mint_price} ETH")

        data = [self.client.address, 1, None]

        for index, item in enumerate(data, 1):
            contract = self.client.get_contract(nft_contract, MINTFUN_ABI[index])
            transaction = await contract.functions.mint(
                item
            ).build_transaction(await self.client.prepare_transaction(value=mint_price))

            return await self.client.send_transaction(transaction)
