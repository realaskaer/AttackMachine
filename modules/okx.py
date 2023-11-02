import hmac
import aiohttp
import base64
import asyncio

from utils.networks import *
from hashlib import sha256
from modules import Client
from datetime import datetime, timezone
from utils.tools import repeater, sleep
from config import OKX_NETWORKS_NAME, OKX_WITHDRAW_LIST
from settings import (
    OKX_API_KEY,
    OKX_API_SECRET,
    OKX_API_PASSPHRAS,
    OKX_NETWORK_ID,
    OKX_AMOUNT_MIN,
    OKX_AMOUNT_MAX,
    OKX_WITHDRAW_NETWORK
)


class OKX(Client):
    def __init__(self, account_number, private_key, _, proxy=None, switch_network=False):
        if switch_network:
            self.network_id = OKX_WITHDRAW_NETWORK
        self.network_id = 6
        super().__init__(account_number, private_key, self.init_network(self.network_id), proxy)
        self.api_key = OKX_API_KEY
        self.api_secret = OKX_API_SECRET
        self.passphras = OKX_API_PASSPHRAS

    @staticmethod
    def init_network(network_id):
        return {
            1: Ethereum,
            2: Arbitrum,
            4: Optimism,
            6: zkSyncEra,
            7: Linea
        }[network_id]


    @staticmethod
    def get_network_name(network_id):
        return {
            1: 'ETHEREUM_MAINNET',
            2: 'ARBITRUM_MAINNET',
            4: 'OPTIMISM_MAINNET',
            7: 'LINEA_MAINNET'
        }[network_id]

    async def get_headers(self, request_path: str, method: str = "GET", body: str = ""):
        try:
            timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            prehash_string = timestamp + method.upper() + request_path[19:] + body
            secret_key_bytes = self.api_secret.encode('utf-8')
            signature = hmac.new(secret_key_bytes, prehash_string.encode('utf-8'), sha256).digest()
            encoded_signature = base64.b64encode(signature).decode('utf-8')

            return {
                "Content-Type": "application/json",
                "OK-ACCESS-KEY": self.api_key,
                "OK-ACCESS-SIGN": encoded_signature,
                "OK-ACCESS-TIMESTAMP": timestamp,
                "OK-ACCESS-PASSPHRASE": self.passphras,
                "x-simulated-trading": "0"
            }
        except Exception as error:
            raise RuntimeError(f'Bad headers for OKX request: {error}')

    async def make_request(self, method:str = 'GET', url:str = None, data:str = None, params: dict = None,
                           headers:dict = None, module_name:str = 'Request'):

        async with aiohttp.ClientSession() as session:
            async with session.request(method=method, url=url, data=data, params=params,
                                       headers=headers, proxy=self.proxy) as response:

                data = await response.json()
                if data['code'] != 0 and data['msg'] != '':
                    error = f"Error code: {data['code']} Msg: {data['msg']}"
                    raise RuntimeError(f"Bad request to OKX({module_name}): {error}")
                else:
                    #self.logger.success(f"{self.info} {module_name}")
                    return data['data']

    async def get_currencies(self):
        url = 'https://www.okx.cab/api/v5/asset/currencies'

        params = {'ccy': 'ETH'}

        headers = await self.get_headers(f'{url}?ccy=ETH')

        return await self.make_request(url=url, headers=headers, params=params, module_name='Token info')

    @repeater
    async def withdraw(self):
        url = 'https://www.okx.cab/api/v5/asset/withdrawal'

        withdraw_data = await self.get_currencies()

        networks_data = {item['chain']: {'can_withdraw': item['canWd'], 'min_fee': item['minFee']} for item in
                         withdraw_data}

        network_name = OKX_NETWORKS_NAME[OKX_NETWORK_ID]
        network_data = networks_data[network_name]
        amount = self.round_amount(OKX_AMOUNT_MIN, OKX_AMOUNT_MAX)

        self.logger.info(f"{self.info} Withdraw {amount} ETH to {network_name[4:]}")

        if network_data['can_withdraw']:

            body = {
                "ccy": 'ETH',
                "amt": amount - float(network_data['min_fee']),
                "dest": "4",
                "toAddr": self.address,
                "fee": network_data['min_fee'],
                "chain": f"{network_name}",
            }

            headers = await self.get_headers(method="POST", request_path=url, body=str(body))

            await self.make_request(method='POST', url=url, data=str(body), headers=headers,
                                    module_name='Withdraw')

            self.logger.success(f"{self.info} Withdraw complete. Note: wait 1-2 minute to receive funds")

            await sleep(self, 70, 140)

        else:
            raise RuntimeError(f"Withdraw {network_name} is not available")

    @repeater
    async def transfer_from_subaccounts(self):
        url_sub_list = "https://www.okx.cab/api/v5/users/subaccount/list"

        headers = await self.get_headers(request_path=url_sub_list)
        sub_list = await self.make_request(url=url_sub_list, headers=headers, module_name='Get subAccounts list')
        await asyncio.sleep(1)

        for sub_data in sub_list:
            sub_name = sub_data['subAcct']

            url_sub_balance = f"https://www.okx.cab/api/v5/asset/subaccount/balances?subAcct={sub_name}&ccy=ETH"
            headers = await self.get_headers(request_path=url_sub_balance)

            sub_balance = (await self.make_request(
                url=url_sub_balance,
                headers=headers,
                module_name='Get subAccount balance'
            ))[0]['availBal']

            await asyncio.sleep(1)

            if float(sub_balance) != 0.0:

                self.logger.info(f'{self.info} {sub_name} | subAccount balance : {sub_balance} ETH')

                body = {
                    "ccy": "ETH",
                    "type": "2",
                    "amt": f"{sub_balance}",
                    "from": "6",
                    "to": "6",
                    "subAcct": sub_name
                }

                url_transfer = "https://www.okx.cab/api/v5/asset/transfer"
                headers = await self.get_headers(method="POST", request_path=url_transfer, body=str(body))
                await self.make_request(method="POST", url=url_transfer, data=str(body), headers=headers,
                                        module_name='SubAccount transfer')

                self.logger.success(f"{self.info} Transfer {sub_balance:.6f} ETH to main account complete")

    @repeater
    async def transfer_from_spot_to_funding(self):

        url_balance = "https://www.okx.cab/api/v5/account/balance?ccy=ETH"
        headers = await self.get_headers(request_path=url_balance)
        balance = (await self.make_request(url=url_balance, headers=headers,
                                           module_name='Trading account'))[0]["details"]

        for ccy in balance:
            if ccy['ccy'] == 'ETH' and ccy['availBal'] != '0':

                self.logger.info(f"{self.info} Main trading account balance: {ccy['availBal']} ETH")

                body = {
                    "ccy": 'ETH',
                    "amt": ccy['availBal'],
                    "from": "18",
                    "to": "6"
                }

                url_transfer = "https://www.okx.cab/api/v5/asset/transfer"
                headers = await self.get_headers(request_path=url_transfer, body=str(body), method="POST")
                await self.make_request(url=url_transfer, data=str(body), method="POST", headers=headers,
                                        module_name='Trading account')
                break
            else:
                self.logger.info(f"{self.info} Main trading account balance: 0 ETH")
                break

    @repeater
    async def deposit_to_okx(self):

        amount, amount_in_wei = await self.check_and_get_eth_for_deposit()

        try:
            okx_wallet = self.w3.to_checksum_address(OKX_WITHDRAW_LIST[self.address])
        except Exception as error:
            raise RuntimeError(f'There is no wallet listed for deposit in OKX: {error}')

        info = f"{okx_wallet[:10]}....{okx_wallet[-6:]}"

        self.logger.info(f"{self.info} Deposit {amount} ETH from {self.network_name} to OKX wallet: {info}")

        tx_params = (await self.prepare_transaction(value=amount_in_wei)) | {
            'to': okx_wallet,
            'data': '0x'
        }

        tx_hash = await self.send_transaction(tx_params)

        await self.verify_transaction(tx_hash)

    async def deposit(self):

        if self.network_id != 6:

            await self.bridge_from_era(self.get_network_name(self.network_id))

            await sleep(self, 60, 80)

        await self.deposit_to_okx()

        await sleep(self, 10, 15)

        await self.transfer_from_subaccounts()

        await self.transfer_from_spot_to_funding()

        self.logger.success(f"{self.info} Deposit complete")
