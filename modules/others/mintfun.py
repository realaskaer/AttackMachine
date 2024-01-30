import random

from web3.exceptions import Web3ValidationError

from modules import Minter, Logger
from config import MINTFUN_ABI
from modules.interfaces import SoftwareException
from utils.tools import helper, gas_checker
from settings import MINTFUN_CONTRACTS


class MintFun(Minter, Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)

    @helper
    @gas_checker
    async def mint(self):

        nft_contract, mint_price = random.choice(list(MINTFUN_CONTRACTS.items()))

        contract = self.client.get_contract(self.client.w3.to_checksum_address(nft_contract), MINTFUN_ABI[1])

        try:
            nft_name = await contract.functions.name().call()
        except:
            nft_name = 'Random'

        self.logger_msg(*self.client.acc_info, msg=f"Mint {nft_name} NFT. Price: {mint_price} ETH")

        data = [self.client.address, 1, None]

        tx_params = await self.client.prepare_transaction(value=mint_price)
        result = False
        counter = 0

        for index, item in enumerate(data, 1):
            try:
                counter += 1
                contract = self.client.get_contract(nft_contract, MINTFUN_ABI[index])
                if item:
                    transaction = await contract.functions.mint(item).build_transaction(tx_params)
                else:
                    transaction = await contract.functions.mint().build_transaction(tx_params)

                result = await self.client.send_transaction(transaction)
            except Web3ValidationError:
                if counter == 3:
                    raise SoftwareException('This mint do not support in software. You need "Mint NFT" function!')

        return result
