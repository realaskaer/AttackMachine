import asyncio
import hmac
import time

from hashlib import sha256
from modules import CEX, Logger
from modules.interfaces import SoftwareExceptionWithoutRetry, SoftwareException
from utils.tools import helper
from config import CEX_WRAPPED_ID, BINGX_NETWORKS_NAME, TOKENS_PER_CHAIN


class BingX(CEX, Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)
        CEX.__init__(self, client, 'BingX')

        self.api_url = "https://open-api.bingx.com"
        self.headers = {
            "Content-Type": "application/json",
            "X-BX-APIKEY": self.api_key,
        }

    @staticmethod
    def parse_params(params: dict | None = None):
        if params:
            sorted_keys = sorted(params)
            params_str = "&".join(["%s=%s" % (x, params[x]) for x in sorted_keys])
        else:
            params_str = ''
        return params_str + "&timestamp=" + str(int(time.time() * 1000))

    def get_sign(self, payload: str = ""):
        try:
            secret_key_bytes = self.api_secret.encode('utf-8')
            signature = hmac.new(secret_key_bytes, payload.encode('utf-8'), sha256).hexdigest()

            return signature
        except Exception as error:
            raise SoftwareExceptionWithoutRetry(f'Bad signature for BingX request: {error}')

    async def get_balance(self, ccy: str):
        path = '/openApi/spot/v1/account/balance'

        params = {
            'timestamp': str(int(time.time() * 1000))
        }

        parse_params = self.parse_params(params)

        url = f"{self.api_url}{path}?{parse_params}&signature={self.get_sign(parse_params)}"
        data = await self.make_request(url=url, headers=self.headers, module_name='Balances Data', content_type=None)
        return [item for item in data['balances'] if item['asset'] == ccy][0]['free']

    async def get_currencies(self, ccy):
        path = '/openApi/wallets/v1/capital/config/getall'

        params = {
            'timestamp': str(int(time.time() * 1000))
        }

        parse_params = self.parse_params(params)

        url = f"{self.api_url}{path}?{parse_params}&signature={self.get_sign(parse_params)}"
        data = await self.make_request(url=url, headers=self.headers, module_name='Token info')
        return [item for item in data if item['coin'] == ccy]

    async def get_sub_list(self):
        path = "/openApi/subAccount/v1/list"

        params = {
            "page": 1,
            "limit": 100,
        }

        await asyncio.sleep(2)
        parse_params = self.parse_params(params)
        url = f"{self.api_url}{path}?{parse_params}&signature={self.get_sign(parse_params)}"
        return await self.make_request(url=url, headers=self.headers, module_name='Get subAccounts list')

    async def get_sub_balance(self, sub_uid):
        path = '/openApi/subAccount/v1/assets'

        params = {
            "subUid": sub_uid
        }

        await asyncio.sleep(2)
        parse_params = self.parse_params(params)
        url = f"{self.api_url}{path}?{parse_params}&signature={self.get_sign(parse_params)}"
        return await self.make_request(url=url, headers=self.headers, module_name='Get subAccount balance')

    async def get_main_balance(self):
        path = '/openApi/spot/v1/account/balance'

        await asyncio.sleep(2)
        parse_params = self.parse_params()
        url = f"{self.api_url}{path}?{parse_params}&signature={self.get_sign(parse_params)}"
        return await self.make_request(url=url, headers=self.headers, content_type=None,
                                       module_name='Get main account balance')

    async def transfer_from_subaccounts(self, ccy: str = 'ETH', amount: float = None):

        if ccy == 'USDC.e':
            ccy = 'USDC'

        self.logger_msg(*self.client.acc_info, msg=f'Checking subAccounts balance')

        flag = True
        sub_list = (await self.get_sub_list())['result']

        for sub_data in sub_list:
            sub_name = sub_data['subAccountString']
            sub_uid = sub_data['subUid']

            sub_balances = await self.get_sub_balance(sub_uid)

            if sub_balances:
                sub_balance = float(
                    [balance for balance in sub_balances['balances'] if balance['asset'] == ccy][0]['free'])

                if sub_balance != 0.0:
                    flag = False
                    self.logger_msg(*self.client.acc_info, msg=f'{sub_name} | subAccount balance : {sub_balance} {ccy}')

                    params = {
                        "amount": amount,
                        "coin": ccy,
                        "userAccount": sub_uid,
                        "userAccountType": 1,
                        "walletType": 1
                    }

                    path = "/openApi/wallets/v1/capital/subAccountInnerTransfer/apply"
                    parse_params = self.parse_params(params)

                    url = f"{self.api_url}{path}?{parse_params}&signature={self.get_sign(parse_params)}"
                    await self.make_request(
                        method="POST", url=url, headers=self.headers, module_name='SubAccount transfer')

                    self.logger_msg(*self.client.acc_info,
                                    msg=f"Transfer {amount} {ccy} to main account complete", type_msg='success')
        if flag:
            self.logger_msg(*self.client.acc_info, msg=f'subAccounts balance: 0 {ccy}', type_msg='warning')
        return True

    async def get_cex_balances(self, ccy: str = 'ETH'):
        while True:
            try:
                if ccy == 'USDC.e':
                    ccy = 'USDC'

                balances = {}

                main_balance = await self.get_main_balance()

                if main_balance:
                    ccy_balance = [balance for balance in main_balance['balances'] if balance['asset'] == ccy]

                    if ccy_balance:
                        balances['Main CEX Account'] = float(ccy_balance[0]['free'])
                    else:
                        balances['Main CEX Account'] = 0
                else:
                    balances['Main CEX Account'] = 0

                sub_list = (await self.get_sub_list())['result']

                for sub_data in sub_list:
                    sub_name = sub_data['subAccountString']
                    sub_uid = sub_data['subUid']
                    sub_balances = await self.get_sub_balance(sub_uid)
                    if sub_balances:
                        ccy_syb_balance = [balance for balance in sub_balances['balances'] if balance['asset'] == ccy]

                        if ccy_syb_balance:
                            balances[sub_name] = float(ccy_syb_balance[0]['free'])
                        else:
                            balances[sub_name] = 0
                    else:
                        balances[sub_name] = 0

                    await asyncio.sleep(3)

                return balances
            except Exception as error:
                if '-1021 Msg: Timestamp for' in str(error):
                    self.logger_msg(
                        *self.client.acc_info,
                        msg=f"Bad timestamp for request. Will try again in 10 second...",
                        type_msg='warning'
                    )
                    await asyncio.sleep(10)
                else:
                    raise error

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

                if acc_balance > old_balances[acc_name]:
                    self.logger_msg(*self.client.acc_info, msg=f"Deposit {amount} {ccy} complete", type_msg='success')
                    return True
                else:
                    continue
            else:
                self.logger_msg(*self.client.acc_info, msg=f"Deposit still in progress...", type_msg='warning')
                await asyncio.sleep(check_time)

    @helper
    async def withdraw(self, want_balance:float = 0, withdraw_data:tuple = None, transfer_mode:bool = False):
        path = '/openApi/wallets/v1/capital/withdraw/apply'

        network_id, amount = withdraw_data
        network_raw_name = BINGX_NETWORKS_NAME[network_id]
        ccy, network_name = network_raw_name.split('-')
        dst_chain_id = CEX_WRAPPED_ID[network_id]

        withdraw_data = (await self.get_currencies(ccy))[0]['networkList']

        network_data = {
            item['network']: {
                'withdrawEnable': item['withdrawEnable'],
                'withdrawFee': item['withdrawFee'],
                'withdrawMin': item['withdrawMin'],
                'withdrawMax': item['withdrawMax']
            } for item in withdraw_data
        }[network_name]

        if transfer_mode:
            amount = await self.get_balance(ccy)
        else:
            amount = want_balance if want_balance else await self.client.get_smart_amount(amount)

        self.logger_msg(
            *self.client.acc_info, msg=f"Withdraw {amount:.5f} {ccy} to {network_name}")

        if network_data['withdrawEnable']:
            min_wd, max_wd = float(network_data['withdrawMin']), float(network_data['withdrawMax'])

            if min_wd <= amount <= max_wd:

                params = {
                    "address": self.client.address,
                    "amount": amount,
                    "coin": ccy,
                    "network": network_name,
                    "walletType": "1",
                }

                ccy = f"{ccy}.e" if network_id in [29, 30] else ccy

                old_balance_on_dst = await self.client.wait_for_receiving(dst_chain_id, token_name=ccy,
                                                                          check_balance_on_dst=True)

                parse_params = self.parse_params(params)
                url = f"{self.api_url}{path}?{parse_params}&signature={self.get_sign(parse_params)}"

                await self.make_request(method='POST', url=url, headers=self.headers, module_name='Withdraw')

                self.logger_msg(*self.client.acc_info,
                                msg=f"Withdraw complete. Note: wait a little for receiving funds", type_msg='success')

                await self.client.wait_for_receiving(dst_chain_id, old_balance_on_dst, token_name=ccy)

                return True
            else:
                raise SoftwareExceptionWithoutRetry(f"Limit range for withdraw: {min_wd:.5f} {ccy} - {max_wd} {ccy}")
        else:
            raise SoftwareExceptionWithoutRetry(f"Withdraw from {network_name} is not available")

    @helper
    async def deposit(self, deposit_data:tuple = None):
        try:
            with open('./data/services/cex_withdraw_list.json') as file:
                from json import load
                cex_withdraw_list = load(file)
        except:
            self.logger_msg(None, None, f"Bad data in cex_wallet_list.json", 'error')

        try:
            cex_wallet = cex_withdraw_list[self.client.account_name]
        except Exception as error:
            raise SoftwareExceptionWithoutRetry(f'There is no wallet listed for deposit to CEX: {error}')

        info = f"{cex_wallet[:10]}....{cex_wallet[-6:]}"

        deposit_network, deposit_amount = deposit_data
        network_raw_name = BINGX_NETWORKS_NAME[deposit_network]
        ccy, network_name = network_raw_name.split('-')
        withdraw_data = (await self.get_currencies(ccy))[0]['networkList']

        network_data = {
            item['network']: {
                'depositEnable': item['depositEnable']
            } for item in withdraw_data
        }[network_name]

        ccy = f"{ccy}.e" if deposit_network in [29, 30] else ccy
        amount = await self.client.get_smart_amount(deposit_amount, token_name=ccy)

        self.logger_msg(*self.client.acc_info, msg=f"Deposit {amount} {ccy} from {network_name} to BingX wallet: {info}")

        if network_data['depositEnable']:

            if ccy != self.client.token:
                token_contract = self.client.get_contract(TOKENS_PER_CHAIN[self.client.network.name][ccy])
                decimals = await self.client.get_decimals(ccy)
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

            result = await self.client.send_transaction(transaction)

            if result:
                await self.wait_deposit_confirmation(amount, cex_balances, ccy=ccy)

                await self.transfer_from_subaccounts(ccy=ccy, amount=amount)
            else:
                raise SoftwareException('Transaction not sent, trying again')

            return result
        else:
            raise SoftwareExceptionWithoutRetry(f"Deposit to {network_name} is not available")
