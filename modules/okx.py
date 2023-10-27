import hmac
import aiohttp
import base64
import asyncio
from utils.networks import Arbitrum
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
    OKX_AMOUNT_MAX
)


class OKX(Client):
    def __init__(self, account_number, private_key, network, proxy=None, switch_network=False):
        if switch_network:
            network = Arbitrum
        super().__init__(account_number, private_key, network, proxy)
        self.api_key = OKX_API_KEY
        self.api_secret = OKX_API_SECRET
        self.passphras = OKX_API_PASSPHRAS
        self.okx_wallet = self.w3.to_checksum_address(OKX_WITHDRAW_LIST[self.address])

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
            self.logger.error(f'{self.info} Bad headers for OKX request: {error}')
            raise

    async def make_request(self, method:str = 'GET', url:str = None, data:str = None, params: dict = None,
                           headers:dict = None, module_name:str = 'Request', module_msg:str = 'Success'):

        async with aiohttp.ClientSession() as session:
            async with session.request(method=method, url=url, data=data, params=params,
                                       headers=headers, proxy=self.proxy) as response:
                data = await response.json()
                if data['code'] != 0 and data['msg'] != '':
                    error = f"Error code: {data['code']} Msg: {data['msg']}"
                    self.logger.error(f"{self.info} OKX | Bad request to OKX({module_name}): {error}")
                    raise
                else:
                    self.logger.success(f"{self.info} OKX | {module_name} | {module_msg}")
                    return data['data']

    async def get_currencies(self):
        url = 'https://www.okx.cab/api/v5/asset/currencies'

        params = {
            'ccy': 'ETH'
        }

        headers = await self.get_headers(f'{url}?ccy=ETH')

        return await self.make_request(url=url, headers=headers, params=params, module_name='Token info',
                                       module_msg='Checking withdrawal availability')

    @repeater
    async def withdraw(self):
        url = 'https://www.okx.cab/api/v5/asset/withdrawal'

        withdraw_data = await self.get_currencies()

        networks_data = {item['chain']: {'can_withdraw': item['canWd'], 'min_fee': item['minFee']} for item in
                         withdraw_data}

        network_name = OKX_NETWORKS_NAME[OKX_NETWORK_ID]
        network_data = networks_data[network_name]
        amount = self.round_amount(OKX_AMOUNT_MIN, OKX_AMOUNT_MAX)

        if network_data['can_withdraw']:

            body = {
                "ccy": 'ETH',
                "amt": amount,
                "dest": "4",
                "toAddr": self.address,
                "fee": network_data['min_fee'],
                "chain": f"{network_name}",
            }

            headers = await self.get_headers(method="POST", request_path=url, body=str(body))

            await self.make_request(method='POST', url=url, data=str(body), headers=headers,
                                    module_name='Withdraw', module_msg=f"Transfer {amount} ETH to {self.address}")
        else:
            self.logger.info(f"{self.info} OKX | Withdraw {network_name} is not available")

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

            self.logger.info(f'{self.info} OKX | {sub_name} | subAccount balance : {sub_balance} ETH')

            if float(sub_balance) != 0.0:

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
                                        module_name='SubAccount transfer',
                                        module_msg=f'Transfer {sub_balance:.6f} ETH to main account complete')
    @repeater
    async def transfer_from_spot_to_funding(self):

        url_balance = "https://www.okx.cab/api/v5/account/balance?ccy=ETH"
        headers = await self.get_headers(request_path=url_balance)
        balance = (await self.make_request(url=url_balance, headers=headers,
                                           module_name='Trading account', module_msg='Checked balance'
                                           ))[0]["details"]

        for ccy in balance:
            if ccy['ccy'] == 'ETH' and ccy['availBal'] != '0':

                self.logger.info(f"{self.info} OKX | Main trading account balance: {ccy['availBal']} ETH")

                body = {
                    "ccy": 'ETH',
                    "amt": ccy['availBal'],
                    "from": "18",
                    "to": "6"
                }

                url_transfer = "https://www.okx.cab/api/v5/asset/transfer"
                headers = await self.get_headers(request_path=url_transfer, body=str(body), method="POST")
                await self.make_request(url=url_transfer, data=str(body), method="POST", headers=headers,
                                        module_name='Trading account', module_msg='Transferred ETH to funding balance')
                break
            else:
                self.logger.info(f"{self.info} OKX | Main trading account balance: 0 ETH")
                break

    @repeater
    async def deposit_to_okx(self):

        amount_in_wei, amount, _ = await self.get_token_balance('ETH')

        info = f"{self.okx_wallet[:10]}....{self.okx_wallet[-6:]}"

        self.logger.info(f"{self.info} OKX | Deposit {amount} ETH from Arbitrum to OKX wallet: {info}")

        tx_params = (await self.prepare_transaction(value=int(amount_in_wei * 0.95))) | {
            'to': self.okx_wallet,
            'data': '0x'
        }

        tx_hash = await self.send_transaction(tx_params)

        await self.verify_transaction(tx_hash)

    async def deposit(self):

        await self.bridge_from_era()

        await sleep(self, 60, 80)

        await self.deposit_to_okx()

        await sleep(self, 10, 15)

        await self.transfer_from_subaccounts()

        await self.transfer_from_spot_to_funding()

        self.logger.success(f"{self.info} OKX | Deposit complete")
