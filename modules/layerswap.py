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

    async def get_available_networks(self):

        url = "https://api.layerswap.io/api/available_networks"

        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, proxy=self.proxy) as response:
                if response.status == 200:
                    return (await response.json())['data']
                else:
                    self.logger.error(f"{self.info} Bad request to LayerSwap(Networks) API: {response.status}")
                    raise

    async def get_swap_rate(self, source_chain: str, destination_chain: str,
                            source_asset: str, destination_asset: str, refuel: bool = False):

        url = "https://api.layerswap.io/api/swap_rate"

        headers = {
            'Content-Type': 'application/json'
        }

        data = {
            "source": source_chain,
            "destination": destination_chain,
            "source_asset": source_asset,
            "destination_asset": destination_asset,
            "refuel": refuel
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url=url, headers=headers, json=data, proxy=self.proxy) as response:
                if response.status == 200:
                    return (await response.json())['data']
                else:
                    self.logger.error(f"{self.info} Bad request to LayerSwap(Swap Rate) API: {response.status}")
                    raise

    async def get_swap_id(self, amount: float, source_chain: str, destination_chain: str,
                          source_asset: str, destination_asset: str, refuel: bool = False):

        url = "https://api.layerswap.io/api/swaps"

        headers = {
            'X-LS-APIKEY': f'{LAYERSWAP_API_KEY}',
            'Content-Type': 'application/json'
        }

        data = {
            "source": source_chain,
            "destination": destination_chain,
            "amount": amount,
            "source_asset": source_asset,
            "destination_asset": destination_asset,
            "destination_address": self.address,
            "refuel": refuel,
            "reference_id": "1"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url=url, headers=headers, json=data, proxy=self.proxy) as response:
                if response.status == 200:
                    return (await response.json())['data']['swap_id']
                else:
                    self.logger.error(f"{self.info} Bad request to LayerSwap(Swap ID) API: {response.status}")
                    raise

    async def prepare_source_transaction(self, tx_id: str):

        url = f"https://api.layerswap.io/api/swaps/{tx_id}/prepare_src_transaction"

        headers = {
            'X-LS-APIKEY': f'{LAYERSWAP_API_KEY}'
        }

        params = {
            'from_address': self.address
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, headers=headers, params=params, proxy=self.proxy) as response:
                if response.status == 200:
                    return (await response.json())['data']
                else:
                    self.logger.error(f"{self.info} Bad request to LayerSwap(Prepare TX) API: {response.status}")
                    raise

    @repeater
    @gas_checker
    async def bridge(self, help_okx:bool = False):

        if help_okx:
            source_chain = LAYERSWAP_CHAIN_NAME[15]
            destination_chain = LAYERSWAP_CHAIN_NAME[2]
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

        data = source_chain, destination_chain, source_asset, destination_asset, refuel

        networks_data = await self.get_available_networks()

        available_for_swap = {
            chain['name']: (assets['asset'], assets['decimals'])
            for chain in networks_data if chain['name'] in [source_chain, destination_chain]
            for assets in chain['currencies'] if assets['asset'] in [source_asset, destination_asset]
        }

        if (len(available_for_swap) == 2 and source_asset in available_for_swap[source_chain]
                and destination_asset in available_for_swap[destination_chain]):

            amount_in_wei = int(amount * 10 ** available_for_swap[source_chain][1])

            min_amount, max_amount, fee_amount = (await self.get_swap_rate(*data)).values()

            if float(min_amount) <= amount <= float(max_amount):

                balance, _, _ = await self.get_token_balance(source_asset)
                if balance >= amount:

                    swap_id = await self.get_swap_id(amount, *data)

                    tx_data = await self.prepare_source_transaction(swap_id)

                    tx_params = (await self.prepare_transaction(value=amount_in_wei)) | {
                        'to': tx_data['to_address'],
                        'data': tx_data['data']
                    }

                    tx_hash = await self.send_transaction(tx_params)

                    await self.verify_transaction(tx_hash)
                else:
                    self.logger.error(f'{self.info} Insufficient balance!')
            else:
                self.logger.error(f'{self.info} Limit range for bridge: {min_amount} - {max_amount} ETH!')
        else:
            self.logger.error(f'{self.info} Bridge {source_asset} {bridge_info} is not active!')
