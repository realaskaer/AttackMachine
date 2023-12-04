from utils.tools import helper, gas_checker
from modules import Minter, Logger
from config import ZKSTARS_CONTRACTS, ZKSTARS_ABI
from settings import ZKSTARS_NFT_CONTRACTS


class ZkStars(Minter, Logger):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.network = self.client.network.name

    async def get_new_nft_id(self):
        for contract_id, contract_address in list(ZKSTARS_CONTRACTS[self.network].items()):
            if contract_id in ZKSTARS_NFT_CONTRACTS or ZKSTARS_NFT_CONTRACTS == 0:
                nft_contract = self.client.get_contract(contract_address=contract_address, abi=ZKSTARS_ABI)
                if not (await nft_contract.functions.balanceOf(self.client.address).call()):
                    return nft_contract, contract_id

        raise RuntimeError('All StarkStars NFT have been minted')

    @helper
    @gas_checker
    async def mint(self):
        nft_contract, contact_id = await self.get_new_nft_id()

        mint_price_in_wei = await nft_contract.functions.getPrice().call()
        mint_price = f"{(mint_price_in_wei / 10 ** 18):.5f}"

        self.logger_msg(*self.client.acc_info, msg=f"Mint zkStars#00{contact_id:0>2} NFT. Price: {mint_price} ETH")

        transaction = await nft_contract.functions.safeMint(
            "0x000000a679C2FB345dDEfbaE3c42beE92c0Fb7A5"
        ).build_transaction(await self.client.prepare_transaction(value=mint_price_in_wei))

        return await self.client.send_transaction(transaction)
