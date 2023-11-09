import hmac
import base64
import asyncio

from hashlib import sha256
from modules import CEX
from datetime import datetime, timezone
from utils.tools import repeater, sleep, gas_checker
from config import OKX_NETWORKS_NAME, OKX_WITHDRAW_LIST
from settings import (
    OKX_WITHDRAW_NETWORK,
    OKX_AMOUNT_MIN,
    OKX_AMOUNT_MAX,
    OKX_DEPOSIT_NETWORK,
    OKX_BRIDGE_NEED
)


class OKX(CEX):
    @staticmethod
    def get_network_id():
        return {
            2: 1,
            4: 7,
            6: 10,
            7: 4
        }[OKX_DEPOSIT_NETWORK]

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

        network_name = OKX_NETWORKS_NAME[OKX_WITHDRAW_NETWORK]
        network_data = networks_data[network_name]
        amount = self.client.round_amount(OKX_AMOUNT_MIN, OKX_AMOUNT_MAX)

        self.client.logger.info(f"{self.client.info} OKX | Withdraw {amount} ETH to {network_name[4:]}")

        if network_data['can_withdraw']:

            body = {
                "ccy": 'ETH',
                "amt": amount - float(network_data['min_fee']),
                "dest": "4",
                "toAddr": self.client.address,
                "fee": network_data['min_fee'],
                "chain": f"{network_name}",
            }

            headers = await self.get_headers(method="POST", request_path=url, body=str(body))

            await self.make_request(method='POST', url=url, data=str(body), headers=headers,
                                    module_name='Withdraw')

            self.client.logger.success(
                f"{self.client.info} OKX | Withdraw complete. Note: wait 1-2 minute to receive funds")

            await sleep(self, 70, 140)

        else:
            raise RuntimeError(f"Withdraw {network_name} is not available")

    @repeater
    async def transfer_from_subaccounts(self):

        self.client.logger.info(f'{self.client.info} OKX | Checking subAccounts balance')

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

                self.client.logger.info(f'{self.client.info} {sub_name} | subAccount balance : {sub_balance} ETH')

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

                self.client.logger.success(
                    f"{self.client.info} OKX | Transfer {float(sub_balance):.6f} ETH to main account complete")

    @repeater
    async def transfer_from_spot_to_funding(self):

        url_balance = "https://www.okx.cab/api/v5/account/balance?ccy=ETH"
        headers = await self.get_headers(request_path=url_balance)
        balance = (await self.make_request(url=url_balance, headers=headers,
                                           module_name='Trading account'))[0]["details"]

        for ccy in balance:
            if ccy['ccy'] == 'ETH' and ccy['availBal'] != '0':

                self.client.logger.info(f"{self.client.info} OKX | Main trading account balance: {ccy['availBal']} ETH")

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
                self.client.logger.success(
                    f"{self.client.info} OKX | Transfer {float(ccy['availBal']):.6f} ETH to funding account complete")
                break
            else:
                self.client.logger.info(f"{self.client.info} OKX | Main trading account balance: 0 ETH")
                break

    @repeater
    @gas_checker
    async def deposit_to_okx(self):

        amount_in_wei, amount, _ = await self.client.get_token_balance()

        try:
            okx_wallet = self.client.w3.to_checksum_address(OKX_WITHDRAW_LIST[self.client.address])
        except Exception as error:
            raise RuntimeError(f'There is no wallet listed for deposit to OKX: {error}')

        info = f"{okx_wallet[:10]}....{okx_wallet[-6:]}"
        network_name = self.client.network.nam

        self.client.logger.info(
            f"{self.client.info} OKX | Deposit {amount * 0.98:.6f} ETH from {network_name} to OKX wallet: {info}")

        tx_params = (await self.client.prepare_transaction(value=int(amount_in_wei * 0.98))) | {
            'to': okx_wallet,
            'data': '0x'
        }

        tx_hash = await self.client.send_transaction(tx_params)

        await self.client.verify_transaction(tx_hash)

    async def deposit(self):

        if OKX_DEPOSIT_NETWORK != 6:

            if OKX_BRIDGE_NEED:
                await self.client.bridge_from_source(self.get_network_id())

                await sleep(self, 60, 80)

        await self.deposit_to_okx()

    @repeater
    async def collect_from_sub(self):

        await self.transfer_from_subaccounts()

        await sleep(self, 5, 10)

        await self.transfer_from_spot_to_funding()
