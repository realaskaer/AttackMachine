from config import SCROLL_NFT_CONTRACT, SCROLL_NFT_ABI
from modules import Logger, Aggregator
from utils.tools import helper, gas_checker


class ScrollNFT(Logger, Aggregator):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)
        Aggregator.__init__(self, client)

        self.contract = self.client.get_contract(SCROLL_NFT_CONTRACT['core'], SCROLL_NFT_ABI)

    async def swap(self):
        pass

    async def get_nft_data(self):
        url = f"https://nft.scroll.io/p/{self.client.address}.json"

        data = await self.make_request(url=url)

        if "metadata" in data:
            return data["metadata"], data["proof"]
        else:
            raise RuntimeError('Scroll Origins NFT Not Found')

    @helper
    @gas_checker
    async def mint(self):
        self.logger_msg(*self.client.acc_info, msg=f'Mint Scroll Origins NFT')

        metadata, proof = await self.get_nft_data()

        transaction = await self.contract.functions.mint(
            self.client.address,
            (
                metadata.get("deployer"),
                metadata.get("firstDeployedContract"),
                metadata.get("bestDeployedContract"),
                int(metadata.get("rarityData", 0), 16),
            ),
            proof
        ).build_transaction(await self.client.prepare_transaction())

        return await self.client.send_transaction(transaction)
