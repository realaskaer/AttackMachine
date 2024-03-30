import asyncio
import hmac
import time

from hashlib import sha256
from modules import CEX, Logger
from modules.interfaces import SoftwareExceptionWithoutRetry, SoftwareException, InsufficientBalanceException
from utils.tools import get_wallet_for_deposit
from config import BINANCE_NETWORKS_NAME, TOKENS_PER_CHAIN, CEX_WRAPPED_ID, TOKENS_PER_CHAIN2


class Binance(CEX, Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)
        CEX.__init__(self, client, 'Binance')

        self.api_url = "https://api.binance.com"
        self.headers = {
            "Content-Type": "application/json",
            "X-MBX-APIKEY": self.api_key,
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
            raise SoftwareExceptionWithoutRetry(f'Bad signature for Binance request: {error}')

    async def get_balance(self, ccy):
        balances = await self.get_main_balance()

        ccy_balance = [balance for balance in balances if balance['asset'] == ccy]

        if ccy_balance:
            return float(ccy_balance[0]['free'])
        raise SoftwareExceptionWithoutRetry(f'Your have not enough {ccy} balance on CEX')

    async def get_currencies(self, ccy):
        path = '/sapi/v1/capital/config/getall'

        params = {
            'timestamp': str(int(time.time() * 1000))
        }

        parse_params = self.parse_params(params)

        url = f"{self.api_url}{path}?{parse_params}&signature={self.get_sign(parse_params)}"
        data = await self.make_request(url=url, headers=self.headers, module_name='Token info')
        return [item for item in data if item['coin'] == ccy]

    async def get_sub_list(self):
        path = "/sapi/v1/sub-account/list"

        parse_params = self.parse_params()
        url = f"{self.api_url}{path}?{parse_params}&signature={self.get_sign(parse_params)}"

        await asyncio.sleep(2)
        return await self.make_request(url=url, headers=self.headers, module_name='Get subAccounts list')

    async def get_sub_balance(self, sub_email):
        path = '/sapi/v3/sub-account/assets'

        params = {
            "email": sub_email
        }

        await asyncio.sleep(2)
        parse_params = self.parse_params(params)
        url = f"{self.api_url}{path}?{parse_params}&signature={self.get_sign(parse_params)}"
        return await self.make_request(url=url, headers=self.headers, module_name='Get subAccount balance')

    async def get_main_balance(self):
        path = '/sapi/v3/asset/getUserAsset'

        await asyncio.sleep(2)
        parse_params = self.parse_params()
        url = f"{self.api_url}{path}?{parse_params}&signature={self.get_sign(parse_params)}"
        return await self.make_request(method='POST', url=url, headers=self.headers, content_type=None,
                                       module_name='Get main account balance')

    async def transfer_from_subaccounts(self, ccy: str = 'ETH', amount: float = None, silent_mode:bool = False):
        if ccy == 'USDC.e':
            ccy = 'USDC'

        if not silent_mode:
            self.logger_msg(*self.client.acc_info, msg=f'Checking subAccounts balance')

        flag = True
        sub_list = (await self.get_sub_list())['subAccounts']

        for sub_data in sub_list:
            sub_email = sub_data['email']

            sub_balances = await self.get_sub_balance(sub_email)
            asset_balances = [balance for balance in sub_balances['balances'] if balance['asset'] == ccy]
            sub_balance = 0.0 if len(asset_balances) == 0 else float(asset_balances[0]['free'])

            amount = amount if amount else sub_balance
            if sub_balance == amount and sub_balance != 0.0:
                flag = False
                self.logger_msg(*self.client.acc_info, msg=f'{sub_email} | subAccount balance : {sub_balance} {ccy}')

                params = {
                    "amount": amount,
                    "asset": ccy,
                    "fromAccountType": "SPOT",
                    "toAccountType": "SPOT",
                    "fromEmail": sub_email
                }

                path = "/sapi/v1/sub-account/universalTransfer"

                while True:
                    try:
                        parse_params = self.parse_params(params)
                        url = f"{self.api_url}{path}?{parse_params}&signature={self.get_sign(parse_params)}"
                        await self.make_request(
                            method="POST", url=url, headers=self.headers, module_name='SubAccount transfer'
                        )

                        break
                    except Exception as error:
                        if 'not reached the required block confirmations' in str(error) or '-9000' in str(error):
                            self.logger_msg(
                                *self.client.acc_info,
                                msg=f"Deposit not reached the required block confirmations. Will try again in 1 min...",
                                type_msg='warning'
                            )
                            await asyncio.sleep(60)
                        elif '-8012 Msg' in str(error):
                            return True
                        else:
                            raise error

                self.logger_msg(
                    *self.client.acc_info, msg=f"Transfer {amount} {ccy} to main account complete", type_msg='success'
                )
                if not silent_mode:
                    break

        if flag and not silent_mode:
            self.logger_msg(*self.client.acc_info, msg=f'subAccounts balance: 0 {ccy}', type_msg='warning')
        return True

    async def get_cex_balances(self, ccy: str = 'ETH'):
        if ccy == 'USDC.e':
            ccy = 'USDC'

        balances = {}

        main_balance = await self.get_main_balance()

        ccy_balance = [balance for balance in main_balance if balance['asset'] == ccy]

        if ccy_balance:
            balances['Main CEX Account'] = float(ccy_balance[0]['free'])
        else:
            balances['Main CEX Account'] = 0

        sub_list = (await self.get_sub_list())['subAccounts']

        for sub_data in sub_list:
            sub_name = sub_data['email']
            sub_balances = await self.get_sub_balance(sub_name)
            ccy_sub_balance = [balance for balance in sub_balances['balances'] if balance['asset'] == ccy]

            if ccy_sub_balance:
                balances[sub_name] = float(ccy_sub_balance[0]['free'])
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
                if acc_balance > old_balances[acc_name]:
                    self.logger_msg(*self.client.acc_info, msg=f"Deposit {amount} {ccy} complete", type_msg='success')
                    return True
                else:
                    continue
            else:
                self.logger_msg(*self.client.acc_info, msg=f"Deposit still in progress...", type_msg='warning')
                await asyncio.sleep(check_time)

    async def withdraw(self, withdraw_data:tuple = None, transfer_mode:bool = False):
        path = '/sapi/v1/capital/withdraw/apply'

        network_id, amount = withdraw_data
        network_raw_name = BINANCE_NETWORKS_NAME[network_id]
        ccy, network_name = network_raw_name.split('-')
        dst_chain_id = CEX_WRAPPED_ID[network_id]

        await self.transfer_from_subaccounts(ccy=ccy, silent_mode=True)

        if isinstance(amount, str):
            amount = self.client.custom_round(await self.get_balance(ccy=ccy) * float(amount), 6)
        else:
            amount = self.client.round_amount(*amount)

        await self.transfer_from_subaccounts(ccy=ccy, silent_mode=True)

        self.logger_msg(*self.client.acc_info, msg=f"Withdraw {amount:.5f} {ccy} to {network_name}")

        while True:
            try:
                withdraw_raw_data = (await self.get_currencies(ccy))[0]['networkList']
                network_data = {
                    item['network']: {
                        'withdrawEnable': item['withdrawEnable'],
                        'withdrawFee': item['withdrawFee'],
                        'withdrawMin': item['withdrawMin'],
                        'withdrawMax': item['withdrawMax']
                    } for item in withdraw_raw_data
                }[network_name]

                if network_data['withdrawEnable']:
                    min_wd, max_wd = float(network_data['withdrawMin']), float(network_data['withdrawMax'])

                    if min_wd <= amount <= max_wd:

                        params = {
                            "address": self.client.address,
                            "amount": amount,
                            "coin": ccy,
                            "network": network_name,
                        }

                        ccy = f"{ccy}.e" if network_id in [29, 30] else ccy

                        omnicheck = True if ccy in ['USDV', 'STG', 'MAV'] else False

                        old_balance_on_dst = await self.client.wait_for_receiving(
                            dst_chain_id, token_name=ccy, omnicheck=omnicheck, check_balance_on_dst=True
                        )

                        parse_params = self.parse_params(params)
                        url = f"{self.api_url}{path}?{parse_params}&signature={self.get_sign(parse_params)}"

                        await self.make_request(method='POST', url=url, headers=self.headers, module_name='Withdraw')

                        self.logger_msg(
                            *self.client.acc_info, msg=f"Withdraw complete. Note: wait a little for receiving funds",
                            type_msg='success'
                        )

                        await self.client.wait_for_receiving(
                            dst_chain_id, old_balance_on_dst, omnicheck=omnicheck, token_name=ccy
                        )
                        return True
                    else:
                        raise SoftwareExceptionWithoutRetry(
                            f"Limit range for withdraw: {min_wd:.5f} {ccy} - {max_wd} {ccy}")
                else:
                    self.logger_msg(
                        *self.client.acc_info,
                        msg=f"Withdraw from {network_name} is not active now. Will try again in 1 min...",
                        type_msg='warning'
                    )
                    await asyncio.sleep(60)
            except InsufficientBalanceException:
                continue

    async def deposit(self, deposit_data: tuple = None):
        cex_wallet = get_wallet_for_deposit(self)
        info = f"{cex_wallet[:10]}....{cex_wallet[-6:]}"
        deposit_network, amount = deposit_data
        network_raw_name = BINANCE_NETWORKS_NAME[deposit_network]
        ccy, network_name = network_raw_name.split('-')
        ccy = f"{ccy}.e" if deposit_network in [29, 30] else ccy

        await self.transfer_from_subaccounts(ccy=ccy, silent_mode=True)

        omnicheck = True if ccy in ['USDV', 'STG', 'MAV'] else False

        self.logger_msg(
            *self.client.acc_info, msg=f"Deposit {amount} {ccy} from {network_name} to Binance wallet: {info}")

        while True:
            try:
                withdraw_data = (await self.get_currencies(ccy))[0]['networkList']
                network_data = {
                    item['network']: {
                        'depositEnable': item['depositEnable']
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

                    # if deposit_network in [29, 30]:
                    #     await self.convert_tokens(deposit_network, 'USDC', amount=amount)
                else:
                    self.logger_msg(
                        *self.client.acc_info,
                        msg=f"Deposit to {network_name} is not active now. Will try again in 1 min...",
                        type_msg='warning'
                    )
                    await asyncio.sleep(60)
            except InsufficientBalanceException:
                continue

    # async def get_converts_list(self, from_token_name, to_token_name):
    #     path = '/sapi/v1/convert/exchangeInfo'
    #
    #     params = {
    #         #'fromAsset': from_token_name,
    #         'toAsset': to_token_name,
    #     }
    #
    #     parse_params = self.parse_params(params=params)
    #     url = f"{self.api_url}{path}?{parse_params}&signature={self.get_sign(parse_params)}"
    #
    #     await asyncio.sleep(5)
    #     return await self.make_request(url=url, headers=self.headers, module_name='Get Tokens Convert List')
    #
    # async def get_convert_id(self, from_token_name, to_token_name, amount):
    #     path = '/sapi/v1/convert/getQuote'
    #
    #     params = {
    #         'fromAsset': from_token_name,
    #         'toAsset': to_token_name,
    #         'fromAmount': amount,
    #     }
    #
    #     parse_params = self.parse_params(params=params)
    #     url = f"{self.api_url}{path}?{parse_params}&signature={self.get_sign(parse_params)}"
    #
    #     await asyncio.sleep(5)
    #     response = await self.make_request(
    #         method="POST", url=url, headers=self.headers, module_name='Prepare Tokens Convert')
    #     print(response)
    #     quote_id = response.get('quoteId')
    #     if quote_id:
    #         return quote_id
    #     raise SoftwareExceptionWithoutRetry('Can`t generate quoteId to convert this pair!')
    #
    # async def accept_convert_id(self, quote_id):
    #     path = '/sapi/v1/convert/acceptQuote'
    #
    #     params = {
    #         'quoteId': quote_id,
    #     }
    #
    #     parse_params = self.parse_params(params=params)
    #     url = f"{self.api_url}{path}?{parse_params}&signature={self.get_sign(parse_params)}"
    #
    #     await asyncio.sleep(5)
    #     response = await self.make_request(method="POST", url=url, headers=self.headers, module_name='Tokens Convert')
    #     print(response)
    #     if response['orderStatus'] == 'SUCCESS':
    #         return response
    #     raise SoftwareExceptionWithoutRetry('Can`t accept this quoteId!')
    #
    # async def convert_tokens(self, network_id, to_token_name, amount):
    #     #from_token_name_cex = await self.get_converts_list(from_token_name, to_token_name)
    #
    #     from_token_name_cex = {
    #         29: 'MATICUSDCE',
    #         30: 'MATICUSDCE'
    #     }[network_id]
    #
    #     quote_id = await self.get_convert_id(from_token_name_cex, to_token_name, amount)
    #     response = await self.accept_convert_id(quote_id)
    #     to_amount = response['toAmount']
    #
    #     self.logger_msg(
    #         *self.client.acc_info, msg=f"Converted {amount} {from_token_name_cex} -> {to_amount} {to_token_name}")
