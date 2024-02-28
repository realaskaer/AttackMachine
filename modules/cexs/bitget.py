import asyncio
import base64
import hmac
import json
import time

from hashlib import sha256

from general_settings import BITGET_API_PASSPHRAS
from modules import CEX, Logger
from modules.interfaces import SoftwareExceptionWithoutRetry, SoftwareException, CriticalException
from utils.tools import helper, get_wallet_for_deposit
from config import CEX_WRAPPED_ID, TOKENS_PER_CHAIN, BITGET_NETWORKS_NAME, TOKENS_PER_CHAIN2


class Bitget(CEX, Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)
        CEX.__init__(self, client, 'Bitget')
        self.api_url = "https://api.bitget.com"

    @staticmethod
    def parse_params(params: dict | None = None):
        if params:
            sorted_keys = sorted(params)
            params_str = f'?{"&".join(["%s=%s" % (x, params[x]) for x in sorted_keys])}'
        else:
            params_str = ''
        return params_str

    def get_headers(self, method:str, api_path:str, params:dict = None, payload:dict | str = ""):
        try:
            timestamp = f"{int(time.time() * 1000)}"
            if method == 'GET':
                api_path = f"{api_path}{self.parse_params(params)}"
                prehash_string = timestamp + method.upper() + api_path
            else:
                prehash_string = timestamp + method.upper() + api_path + json.dumps(payload)

            secret_key_bytes = self.api_secret.encode('utf8')
            signature = hmac.new(secret_key_bytes, prehash_string.encode('utf8'), sha256).digest()
            encoded_signature = base64.standard_b64encode(signature).decode('utf8')

            return {
                "ACCESS-KEY": self.api_key,
                "ACCESS-SIGN": encoded_signature,
                "ACCESS-PASSPHRASE": BITGET_API_PASSPHRAS,
                "ACCESS-TIMESTAMP": timestamp,
                "locale": "en-US",
                "Content-Type": "application/json"
            }
        except Exception as error:
            raise SoftwareExceptionWithoutRetry(f'Bad headers for BitGet request: {error}')

    async def get_balance(self, ccy: str):
        path = '/api/v2/spot/account/assets'

        params = {
            'coin': ccy
        }

        url = f"{self.api_url}{path}"
        data = await self.make_request(url=url, params=params, module_name='Balances Data')
        return data[0]['available']

    async def get_currencies(self, ccy):
        path = '/api/v2/spot/public/coins'

        params = {
            'coin': ccy
        }

        url = f"{self.api_url}{path}"
        return await self.make_request(url=url, params=params, module_name='Token info')

    async def get_sub_balances(self):
        path = "/api/v2/spot/account/subaccount-assets"

        await asyncio.sleep(2)
        url = f"{self.api_url}{path}"
        headers = self.get_headers('GET', path)
        return await self.make_request(url=url, headers=headers, module_name='Get subAccounts balances')

    async def get_main_info(self):
        path = '/api/v2/spot/account/info'

        await asyncio.sleep(2)
        url = f"{self.api_url}{path}"
        headers = self.get_headers('GET', path)
        return await self.make_request(url=url, headers=headers, module_name='Get main account info')

    async def get_main_balance(self, ccy):
        path = '/api/v2/spot/account/assets'

        params = {
            'coin': ccy
        }

        url = f"{self.api_url}{path}"
        headers = self.get_headers('GET', path, params=params)
        return await self.make_request(url=url, params=params, headers=headers, module_name='Main account balance')

    async def transfer_from_subaccounts(self, ccy: str = 'ETH', amount: float = None):

        if ccy == 'USDC.e':
            ccy = 'USDC'

        self.logger_msg(*self.client.acc_info, msg=f'Checking subAccounts balance')

        flag = True
        sub_list = await self.get_sub_balances()
        main_id = (await self.get_main_info())['userId']

        for sub_data in sub_list:
            sub_id = sub_data['userId']
            sub_balances = sub_data['assetsList']
            ccy_sub_balance = [balance for balance in sub_balances if balance['coin'] == ccy]

            if ccy_sub_balance:
                ccy_sub_balance = float(ccy_sub_balance[0]['available'])

                if ccy_sub_balance != 0.0:
                    flag = False
                    self.logger_msg(
                        *self.client.acc_info, msg=f'{sub_id} | subAccount balance : {ccy_sub_balance} {ccy}')

                    if ccy_sub_balance < amount:
                        amount = ccy_sub_balance

                    payload = {
                        "fromType": "spot",
                        "toType": "spot",
                        "amount": f"{amount}",
                        "coin": f"{ccy}",
                        "fromUserId": f"{sub_id}",
                        "toUserId": f"{main_id}",
                    }

                    path = "/api/v2/spot/wallet/subaccount-transfer"
                    url = f"{self.api_url}{path}"
                    headers = self.get_headers('POST', path, payload=payload)
                    await self.make_request(
                        method="POST", url=url, json=payload, headers=headers, module_name='SubAccount transfer')

                    self.logger_msg(*self.client.acc_info,
                                    msg=f"Transfer {amount} {ccy} to main account complete", type_msg='success')
        if flag:
            self.logger_msg(*self.client.acc_info, msg=f'subAccounts balance: 0 {ccy}', type_msg='warning')
        return True

    async def get_cex_balances(self, ccy: str = 'ETH'):

        if ccy == 'USDC.e':
            ccy = 'USDC'

        balances = {}

        main_balances = await self.get_main_balance(ccy)

        ccy_balance = [balance for balance in main_balances if balance['coin'] == ccy]

        if ccy_balance:
            balances['Main CEX Account'] = float(ccy_balance[0]['available'])
        else:
            balances['Main CEX Account'] = 0

        sub_list = await self.get_sub_balances()

        for sub_data in sub_list:
            sub_name = sub_data['userId']
            sub_balances = sub_data['assetsList']
            ccy_sub_balance = [balance for balance in sub_balances if balance['coin'] == ccy]

            if ccy_sub_balance:
                balances[sub_name] = float(ccy_sub_balance[0]['available'])
            else:
                balances[sub_name] = 0

            await asyncio.sleep(3)

        return balances

    async def wait_deposit_confirmation(
            self, amount: float, old_balances: dict, ccy: str = 'ETH', check_time: int = 45
    ):

        if ccy == 'USDC.e':
            ccy = 'USDC'

        self.logger_msg(*self.client.acc_info, msg=f"Start checking CEX balances")

        await asyncio.sleep(10)
        while True:
            new_sub_balances = await self.get_cex_balances(ccy=ccy)
            for acc_name, acc_balance in new_sub_balances.items():
                if acc_name not in old_balances:
                    old_balances[acc_name] = 0
                if acc_balance > old_balances[acc_name]:
                    self.logger_msg(*self.client.acc_info, msg=f"Deposit {amount} {ccy} complete", type_msg='success')
                    return True
                else:
                    continue
            else:
                self.logger_msg(*self.client.acc_info, msg=f"Deposit still in progress...", type_msg='warning')
                await asyncio.sleep(check_time)

    @helper
    async def withdraw(self, withdraw_data:tuple = None):
        path = '/api/v2/spot/wallet/withdrawal'

        network_id, amount = withdraw_data
        network_raw_name = BITGET_NETWORKS_NAME[network_id]
        split_network_data = network_raw_name.split('-')
        ccy, network_name = split_network_data[0], '-'.join(split_network_data[1:])
        dst_chain_id = CEX_WRAPPED_ID[network_id]
        amount = self.client.round_amount(*amount)

        self.logger_msg(*self.client.acc_info, msg=f"Withdraw {amount:.5f} {ccy} to {network_name}")

        while True:
            withdraw_raw_data = (await self.get_currencies(ccy))[0]['chains']
            network_data = {
                item['chain']: {
                    'withdrawEnable': item['withdrawable'],
                    'withdrawFee': item['withdrawFee'],
                    'withdrawMin': item['minWithdrawAmount'],
                } for item in withdraw_raw_data
            }[network_name]

            if network_data['withdrawEnable']:
                min_wd = float(network_data['withdrawMin'])

                if min_wd <= amount:

                    payload = {
                        "coin": ccy,
                        "address": self.client.address.lower(),
                        "chain": network_name,
                        "size": f"{amount}",
                        "transferType": 'on_chain',
                    }

                    ccy = f"{ccy}.e" if network_id in [29, 30] else ccy

                    omnicheck = False
                    if ccy in ['USDV', 'STG']:
                        omnicheck = True

                    old_balance_on_dst = await self.client.wait_for_receiving(
                        dst_chain_id, token_name=ccy, omnicheck=omnicheck, check_balance_on_dst=True
                    )

                    url = f"{self.api_url}{path}"
                    headers = self.get_headers('POST', path, payload=payload)
                    await self.make_request(
                        method='POST', url=url, headers=headers, json=payload, module_name='Withdraw')

                    self.logger_msg(*self.client.acc_info,
                                    msg=f"Withdraw complete. Note: wait a little for receiving funds",
                                    type_msg='success')

                    await self.client.wait_for_receiving(
                        dst_chain_id, old_balance_on_dst, omnicheck=omnicheck, token_name=ccy
                    )

                    return True
                else:
                    raise SoftwareExceptionWithoutRetry(f"Limit range for withdraw: more than {min_wd:.5f} {ccy}")
            else:
                self.logger_msg(
                    *self.client.acc_info,
                    msg=f"Withdraw from {network_name} is not active now. Will try again in 1 min...",
                    type_msg='warning'
                )
                await asyncio.sleep(60)

    @helper
    async def deposit(self, deposit_data:tuple = None):
        cex_wallet = get_wallet_for_deposit(self)
        info = f"{cex_wallet[:10]}....{cex_wallet[-6:]}"
        deposit_network, amount = deposit_data
        network_raw_name = BITGET_NETWORKS_NAME[deposit_network]
        ccy, network_name = network_raw_name.split('-')
        if deposit_network in [29, 30]:
            ccy = f"{ccy}.e"

        omnicheck = False
        if ccy in ['USDV', 'STG']:
            omnicheck = True

        self.logger_msg(
            *self.client.acc_info, msg=f"Deposit {amount} {ccy} from {network_name} to Bitget wallet: {info}")

        while True:

            withdraw_data = (await self.get_currencies(ccy))[0]['chains']
            network_data = {
                item['chain']: {
                    'depositEnable': item['rechargeable']
                } for item in withdraw_data
            }[network_name]

            if network_data['depositEnable']:

                if ccy != self.client.token:
                    if omnicheck:
                        token_contract = self.client.get_contract(TOKENS_PER_CHAIN2[self.client.network.name][ccy])
                    else:
                        token_contract = self.client.get_contract(TOKENS_PER_CHAIN[self.client.network.name][ccy])
                    decimals = await self.client.get_decimals(ccy, omnicheck=omnicheck)
                    amount_in_wei = self.client.to_wei(amount, decimals)

                    transaction = await token_contract.functions.transfer(
                        self.client.w3.to_checksum_address(cex_wallet),
                        amount_in_wei
                    ).build_transaction(await self.client.prepare_transaction())
                else:
                    amount_in_wei = self.client.to_wei(amount)
                    transaction = (await self.client.prepare_transaction(value=int(amount_in_wei))) | {
                        'to': self.client.w3.to_checksum_address(cex_wallet),
                        'data': '0x'
                    }

                cex_balances = await self.get_cex_balances(ccy=ccy)

                result_tx = await self.client.send_transaction(transaction)

                if result_tx:
                    result_confirmation = await self.wait_deposit_confirmation(amount, cex_balances, ccy=ccy)

                    result_transfer = await self.transfer_from_subaccounts(ccy=ccy, amount=amount)

                    return all([result_tx, result_confirmation, result_transfer])
                else:
                    raise SoftwareException('Transaction not sent, trying again')
            else:
                self.logger_msg(
                    *self.client.acc_info,
                    msg=f"Deposit to {network_name} is not active now. Will try again in 1 min...",
                    type_msg='warning'
                )
                await asyncio.sleep(60)
