import asyncio
import copy
import random

from modules import Minter, Logger, RequestClient
from config import MINTFUN_ABI
from modules.interfaces import SoftwareException
from utils.tools import helper, gas_checker
from settings import MINTFUN_CONTRACTS, MINTFUN_MINT_COUNT


class MintFun(Minter, Logger, RequestClient):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)
        RequestClient.__init__(self, client)

    async def get_tx_data(self, contract_address):
        url = f'https://mint.fun/api/mintfun/contract/{self.client.network.chain_id}:{contract_address}/transactions'

        params = {
            'address': self.client.address
        }

        response = await self.make_request(url=url, params=params)

        total_time = 0
        timeout = 10
        while True:
            for tx in response['transactions']:
                if int(tx['nftCount']) == 1 and tx['to'].lower() == contract_address.lower() and tx['isValid']:
                    calldata = tx['callData'].replace(
                        'ec45d2d56ec37ffabeb503a27ae21ba806ebe075', self.client.address[2:])
                    eth_value = int(tx['ethValue'])

                    return calldata, eth_value

            total_time += 10
            await asyncio.sleep(10)

            if total_time > timeout:
                raise SoftwareException('Mint.fun have not data for this mint!')

    @helper
    @gas_checker
    async def mint(self):
        mint_contracts = copy.deepcopy(MINTFUN_CONTRACTS)
        random.shuffle(mint_contracts)
        mints_count = random.randint(*copy.deepcopy(MINTFUN_MINT_COUNT))

        for index, nft_contract in enumerate(mint_contracts[:mints_count]):
            try:
                nft_contract = self.client.w3.to_checksum_address(nft_contract)

                calldata, eth_value = await self.get_tx_data(nft_contract)

                contract = self.client.get_contract(self.client.w3.to_checksum_address(nft_contract), MINTFUN_ABI[1])

                try:
                    nft_name = await contract.functions.name().call()
                except:
                    nft_name = 'Random'

                self.logger_msg(*self.client.acc_info, msg=f"Mint {nft_name} NFT. Price: {eth_value / 10 ** 18:.6f} ETH")

                transaction = await self.client.prepare_transaction(value=eth_value) | {
                    'to': nft_contract,
                    'data': f"0x{calldata}"
                }

                return await self.client.send_transaction(transaction)

            except Exception as error:
                self.logger_msg(
                    *self.client.acc_info,
                    msg=f"Impossible to mint NFT on contract address '{nft_contract}'. Error: {error}", type_msg='error'
                )
