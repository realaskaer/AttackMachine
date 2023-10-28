import json
import random
import aiohttp

from modules import Client
from utils.networks import *
from utils.tools import gas_checker, repeater
from config import LAYERSWAP_CHAIN_NAME
from settings import (
    LAYERSWAP_API_KEY,
    LAYERSWAP_TOKEN_FROM,
    LAYERSWAP_TOKEN_TO,
    LAYERSWAP_AMOUNT_MIN,
    LAYERSWAP_AMOUNT_MAX,
    LAYERSWAP_CHAIN_ID_FROM,
    LAYERSWAP_CHAIN_ID_TO,
    LAYERSWAP_REFUEL
)


class LayerSwap(Client):
    def __init__(self, account_number, private_key, _, proxy=None, help_okx=False):
        self.source_chain_id = random.choice(LAYERSWAP_CHAIN_ID_FROM)
        if help_okx:
            self.source_chain_id = 15
        super().__init__(account_number, private_key, self.network_init(self.source_chain_id), proxy)

    @staticmethod
    def network_init(source_chain_id):
        return {
            1: Arbitrum_nova,
            2: Arbitrum,
            3: Avalanche,
            4: Base,
            5: BSC,
            6: Ethereum,
            7: Linea,
            8: Manta,
            9: Mantle,
            10: OpBNB,
            11: Optimism,
            12: Polygon_ZKEVM,
            13: Polygon,
            14: Scroll,
            15: zkSyncEra,
            #  16: zkSyncEra,  # lite bridge to layerswap wallet
            17: Zora,
        }[source_chain_id]

    async def make_request(self, url:str, method:str = 'GET', params:dict = None,
                           data:dict = None, module_name:str = 'Request'):

        headers = {
            'X-LS-APIKEY': f'{LAYERSWAP_API_KEY}',
            'Content-Type': 'application/json'
        }

        async with aiohttp.ClientSession() as session:
            async with session.request(method=method, url=url, headers=headers, data=json.dumps(data),
                                       params=params, proxy=self.proxy) as response:

                data = await response.json()
                if data['error'] is None:
                    #  self.logger.success(f"{self.info} LayerSwap | {module_name} | Success")
                    return (await response.json())['data']
                raise RuntimeError(f"Bad request to LayerSwap({module_name}) API: {data['error']}")

    @repeater
    @gas_checker
    async def bridge(self, help_okx:bool = False):

        if help_okx:
            source_chain, destination_chain = 'ZKSYNCERA_MAINNET', 'ARBITRUM_MAINNET'
            source_asset, destination_asset = 'ETH', 'ETH'
            amount, _ = await self.check_and_get_eth_for_deposit()
            refuel = False
        else:
            source_chain = LAYERSWAP_CHAIN_NAME[self.source_chain_id]
            destination_chain = LAYERSWAP_CHAIN_NAME[random.choice(LAYERSWAP_CHAIN_ID_TO)]
            source_asset, destination_asset = LAYERSWAP_TOKEN_FROM, LAYERSWAP_TOKEN_TO
            amount = self.round_amount(LAYERSWAP_AMOUNT_MIN, LAYERSWAP_AMOUNT_MAX)
            refuel = LAYERSWAP_REFUEL

        bridge_info = f'{source_chain.capitalize()[:-8]} -> {destination_asset} {destination_chain.capitalize()[:-8]}'
        self.logger.info(f'{self.info} Bridge on LayerSwap: {amount} {source_asset} {bridge_info}')

        url_network_data = "https://api.layerswap.io/api/available_networks"

        networks_data = await self.make_request(url=url_network_data, module_name='Networks data')

        available_for_swap = {
            chain['name']: (assets['asset'], assets['decimals'])
            for chain in networks_data if chain['name'] in [source_chain, destination_chain]
            for assets in chain['currencies'] if assets['asset'] in [source_asset, destination_asset]
        }

        if (len(available_for_swap) == 2 and source_asset in available_for_swap[source_chain]
                and destination_asset in available_for_swap[destination_chain]):

            url_swap_rate = "https://api.layerswap.io/api/swap_rate"

            swap_rate_data = {
                "source": source_chain,
                "destination": destination_chain,
                "source_asset": source_asset,
                "destination_asset": destination_asset,
                "refuel": refuel
            }

            min_amount, max_amount, fee_amount = (await self.make_request(method='POST', url=url_swap_rate,
                                                                          data=swap_rate_data,
                                                                          module_name='Swap rate')).values()

            if float(min_amount) <= amount <= float(max_amount):

                _, balance, _ = await self.get_token_balance(source_asset)

                if balance >= amount:

                    url_create_swap = "https://api.layerswap.io/api/swaps"

                    create_swap_data = swap_rate_data | {
                        "amount": amount,
                        "destination_address": self.address,
                        "refuel": refuel
                    }

                    swap_id = (await self.make_request(method='POST', url=url_create_swap, data=create_swap_data,
                                                       module_name='Create swap'))['swap_id']

                    params = {'from_address': self.address}

                    url_prepare_tx = f"https://api.layerswap.io/api/swaps/{swap_id}/prepare_src_transaction"

                    tx_data = await self.make_request(url=url_prepare_tx, params=params, module_name='Prepare TX')

                    amount_in_wei = int(amount * 10 ** available_for_swap[source_chain][1])

                    tx_params = (await self.prepare_transaction(value=amount_in_wei)) | {
                        'to': tx_data['to_address'],
                        'data': tx_data['data']
                    }

                    tx_hash = await self.send_transaction(tx_params)

                    await self.verify_transaction(tx_hash)
                else:
                    raise RuntimeError("Insufficient balance!")
            else:
                raise RuntimeError(f"Limit range for bridge: {min_amount} - {max_amount} ETH")
        else:
            raise RuntimeError(f"Bridge {source_asset} {bridge_info} is not active!")
