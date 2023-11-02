import aiohttp
import random

from utils.networks import *
from modules import Client
from utils.tools import repeater, gas_checker
from config import ORBITER_CHAINS_INFO
from settings import (
    ORBITER_TOKEN_NAME,
    ORBITER_AMOUNT_MIN,
    ORBITER_AMOUNT_MAX,
    ORBITER_CHAIN_ID_FROM,
    ORBITER_CHAIN_ID_TO,
)


class Orbiter(Client):
    def __init__(self, account_number, private_key, _, proxy=None):
        self.from_chain_id = random.choice(ORBITER_CHAIN_ID_FROM)
        super().__init__(account_number, private_key, self.network_init(self.from_chain_id), proxy)

    @staticmethod
    def network_init(source_chain_id):
        return {
            1: Arbitrum,
            2: Arbitrum_nova,
            3: BSC,
            4: Base,
            5: Ethereum,
            6: Linea,
            7: Manta,
            8: Mantle,
            9: OpBNB,
            10: Optimism,
            11: Polygon,
            12: Polygon_ZKEVM,
            13: Scroll,
            14: Zora,
            15: zkSyncEra,
            #  16: zkSyncEra,  # lite bridge to orbiter wallet to-do
        }[source_chain_id]

    async def get_bridge_data(self, from_chain: int, to_chain:int, token_name: str):

        url = 'https://openapi.orbiter.finance/explore/v3/yj6toqvwh1177e1sexfy0u1pxx5j8o47'

        request_data = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "orbiter_getTradingPairs",
            "params": []
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=request_data, proxy=self.proxy) as response:
                if response.status == 201:
                    data = (await response.json())['result']['ruleList']
                    bridge_data = {}

                    path = f'{from_chain}-{to_chain}:{token_name}-{token_name}'

                    for chain_data in data:
                        if chain_data['pairId'] == path:
                            bridge_data = {
                                'maker': chain_data['sender'],
                                'fee': chain_data['tradingFee'],
                                'decimals': chain_data['fromChain']['decimals'],
                                'min_amount': chain_data['fromChain']['minPrice'],
                                'max_amount': chain_data['fromChain']['maxPrice'],
                            }
                    if bridge_data:
                        return bridge_data
                    raise RuntimeError(f'That bridge is not active!')
                raise RuntimeError(f'Bad request to Orbiter API: {response.status}')

    @repeater
    @gas_checker
    async def bridge(self):

        from_chain = ORBITER_CHAINS_INFO[self.from_chain_id]
        to_chain = ORBITER_CHAINS_INFO[random.choice(ORBITER_CHAIN_ID_TO)]
        token_name = ORBITER_TOKEN_NAME
        amount = self.round_amount(ORBITER_AMOUNT_MIN, ORBITER_AMOUNT_MAX)

        self.logger.info(
            f'{self.info} Bridge on Orbiter: {amount} {token_name} from {from_chain["name"]} to {to_chain["name"]}')

        bridge_data = await self.get_bridge_data(from_chain['chainId'], to_chain['chainId'], token_name)
        destination_code = 9000 + to_chain['id']
        fee = int(float(bridge_data['fee']) * 10 ** bridge_data['decimals'])
        min_price, max_price = bridge_data['min_amount'], bridge_data['max_amount']
        amount_in_wei = int(amount * 10 ** bridge_data['decimals'])

        tx_params = (await self.prepare_transaction(value=amount_in_wei + destination_code + fee)) | {
            'to': bridge_data['maker']
        }

        if min_price <= amount <= max_price:

            _, balance_in_wei, _ = await self.get_token_balance(token_name)
            if balance_in_wei >= tx_params['value']:

                tx_hash = await self.send_transaction(tx_params)

                await self.verify_transaction(tx_hash)

            else:
                raise RuntimeError(f'Insufficient balance!')
        else:
            raise RuntimeError(f"Limit range for bridge: {min_price} – {max_price} {token_name}!")
