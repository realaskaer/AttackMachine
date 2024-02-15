import hmac
import base64
import asyncio

from hashlib import sha256
from modules import CEX, Logger
from datetime import datetime, timezone

from modules.interfaces import SoftwareExceptionWithoutRetry
from utils.tools import helper, sleep
from config import OKX_NETWORKS_NAME, TOKENS_PER_CHAIN, CEX_WRAPPED_ID


class OKX(CEX, Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)
        CEX.__init__(self, client, "OKX")

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
            raise SoftwareExceptionWithoutRetry(f'Bad headers for OKX request: {error}')

    async def get_currencies(self, ccy: str = 'ETH'):
        url = 'https://www.okx.cab/api/v5/asset/currencies'

        params = {'ccy': ccy}

        headers = await self.get_headers(f'{url}?ccy={ccy}')

        return await self.make_request(url=url, headers=headers, params=params, module_name='Token info')

    @helper
    async def withdraw(self, want_balance:float = 0, withdraw_data:tuple = None):

        url = 'https://www.okx.cab/api/v5/asset/withdrawal'

        network, amount = withdraw_data
        network_raw_name = OKX_NETWORKS_NAME[network]
        ccy, network_name = network_raw_name.split('-')
        dst_chain_id = CEX_WRAPPED_ID[network]

        await self.transfer_from_subs(ccy=ccy)

        withdraw_data = await self.get_currencies(ccy)

        network_data = {
            item['chain']: {
                'can_withdraw': item['canWd'],
                'min_fee': item['minFee'],
                'min_wd': item['minWd'],
                'max_wd': item['maxWd']
            } for item in withdraw_data
        }[network_raw_name]

        amount = await self.client.get_smart_amount(amount)

        self.logger_msg(
            *self.client.acc_info, msg=f"Withdraw {amount} {ccy} to {network_name}")

        if network_data['can_withdraw']:
            min_wd, max_wd = float(network_data['min_wd']), float(network_data['max_wd'])

            if min_wd <= amount <= max_wd:

                body = {
                    "ccy": ccy,
                    "amt": amount,
                    "dest": "4",
                    "toAddr": self.client.address,
                    "fee": network_data['min_fee'],
                    "chain": network_raw_name,
                }

                headers = await self.get_headers(method="POST", request_path=url, body=str(body))

                ccy = f"{ccy}.e" if network in [29, 30] else ccy

                old_balance_on_dst = await self.client.wait_for_receiving(dst_chain_id, token_name=ccy,
                                                                          check_balance_on_dst=True)

                await self.make_request(method='POST', url=url, data=str(body), headers=headers, module_name='Withdraw')

                self.logger_msg(*self.client.acc_info,
                                msg=f"Withdraw complete. Note: wait a little for receiving funds", type_msg='success')

                await self.client.wait_for_receiving(dst_chain_id, old_balance_on_dst, token_name=ccy)

                return True
            else:
                raise SoftwareExceptionWithoutRetry(f"Limit range for withdraw: {min_wd:.5f} {ccy} - {max_wd} {ccy}")
        else:
            raise SoftwareExceptionWithoutRetry(f"Withdraw from {network_name} is not available")

    @helper
    async def transfer_from_subaccounts(self, ccy:str = 'ETH', amount:float = None):

        if ccy == 'USDC.e':
            ccy = 'USDC'

        self.logger_msg(*self.client.acc_info, msg=f'Checking subAccounts balance')

        url_sub_list = "https://www.okx.cab/api/v5/users/subaccount/list"

        flag = True
        headers = await self.get_headers(request_path=url_sub_list)
        sub_list = await self.make_request(url=url_sub_list, headers=headers, module_name='Get subAccounts list')
        await asyncio.sleep(1)

        for sub_data in sub_list:
            sub_name = sub_data['subAcct']

            url_sub_balance = f"https://www.okx.cab/api/v5/asset/subaccount/balances?subAcct={sub_name}&ccy={ccy}"
            headers = await self.get_headers(request_path=url_sub_balance)

            sub_balance = (await self.make_request(url=url_sub_balance, headers=headers,
                                                   module_name='Get subAccount balance'))

            if sub_balance:
                sub_balance = float(sub_balance[0]['availBal'])

            await asyncio.sleep(1)

            if sub_balance != 0.0:
                flag = False
                amount = amount if amount else sub_balance
                self.logger_msg(*self.client.acc_info, msg=f'{sub_name} | subAccount balance : {sub_balance} {ccy}')

                body = {
                    "ccy": ccy,
                    "type": "2",
                    "amt": f"{amount}",
                    "from": "6",
                    "to": "6",
                    "subAcct": sub_name
                }

                url_transfer = "https://www.okx.cab/api/v5/asset/transfer"
                headers = await self.get_headers(method="POST", request_path=url_transfer, body=str(body))
                await self.make_request(method="POST", url=url_transfer, data=str(body), headers=headers,
                                        module_name='SubAccount transfer')

                self.logger_msg(*self.client.acc_info,
                                msg=f"Transfer {amount} {ccy} to main account complete", type_msg='success')
        if flag:
            self.logger_msg(*self.client.acc_info, msg=f'subAccounts balance: 0 {ccy}', type_msg='warning')
        return True

    @helper
    async def transfer_from_spot_to_funding(self, ccy:str = 'ETH'):

        if ccy == 'USDC.e':
            ccy = 'USDC'

        url_balance = f"https://www.okx.cab/api/v5/account/balance?ccy={ccy}"
        headers = await self.get_headers(request_path=url_balance)
        balance = (await self.make_request(url=url_balance, headers=headers,
                                           module_name='Trading account'))[0]["details"]

        for ccy_item in balance:
            if ccy_item['ccy'] == ccy and ccy_item['availBal'] != '0':

                self.logger_msg(
                    *self.client.acc_info, msg=f"Main trading account balance: {ccy_item['availBal']} {ccy}")

                body = {
                    "ccy": ccy,
                    "amt": ccy_item['availBal'],
                    "from": "18",
                    "to": "6"
                }

                url_transfer = "https://www.okx.cab/api/v5/asset/transfer"
                headers = await self.get_headers(request_path=url_transfer, body=str(body), method="POST")
                await self.make_request(url=url_transfer, data=str(body), method="POST", headers=headers,
                                        module_name='Trading account')
                self.logger_msg(*self.client.acc_info,
                                msg=f"Transfer {float(ccy_item['availBal']):.6f} {ccy} to funding account complete",
                                type_msg='success')
                break
            else:
                self.logger_msg(*self.client.acc_info, msg=f"Main trading account balance: 0 {ccy}", type_msg='warning')
                break

        return True

    async def get_cex_balances(self, ccy:str = 'ETH'):
        balances = {}
        url_sub_list = "https://www.okx.cab/api/v5/users/subaccount/list"

        await asyncio.sleep(10)

        if ccy == 'USDC.e':
            ccy = 'USDC'

        headers = await self.get_headers(request_path=url_sub_list)
        sub_list = await self.make_request(url=url_sub_list, headers=headers, module_name='Get subAccounts list')

        url_balance = f"https://www.okx.cab/api/v5/asset/balances?ccy={ccy}"

        headers = await self.get_headers(request_path=url_balance)

        balance = (await self.make_request(url=url_balance, headers=headers, module_name='Get Account balance'))

        if balance:
            balances['Main CEX Account'] = float(balance[0]['availBal'])

        for sub_data in sub_list:
            sub_name = sub_data['subAcct']

            url_sub_balance = f"https://www.okx.cab/api/v5/asset/subaccount/balances?subAcct={sub_name}&ccy={ccy}"
            headers = await self.get_headers(request_path=url_sub_balance)

            sub_balance = (await self.make_request(url=url_sub_balance, headers=headers,
                                                   module_name='Get subAccount balance'))
            await asyncio.sleep(3)

            if sub_balance:
                balances[sub_name] = float(sub_balance[0]['availBal'])

        return balances

    async def wait_deposit_confirmation(self, amount:float, old_sub_balances:dict, ccy:str = 'ETH',
                                        check_time:int = 45, timeout:int = 1200):

        if ccy == 'USDC.e':
            ccy = 'USDC'

        self.logger_msg(*self.client.acc_info, msg=f"Start checking CEX balances")

        await asyncio.sleep(10)
        total_time = 0
        while total_time < timeout:
            new_sub_balances = await self.get_cex_balances(ccy=ccy)
            for sub_name, sub_balance in new_sub_balances.items():
                if sub_balance > old_sub_balances[sub_name]:
                    self.logger_msg(*self.client.acc_info, msg=f"Deposit {amount} {ccy} complete", type_msg='success')
                    return True
                else:
                    continue
            else:
                total_time += check_time
                self.logger_msg(*self.client.acc_info, msg=f"Deposit still in progress...", type_msg='warning')
                await asyncio.sleep(check_time)

        self.logger_msg(*self.client.acc_info, msg=f"Deposit does not complete in {timeout} seconds", type_msg='error')

    @helper
    async def deposit(self, deposit_data:tuple = None):
        try:
            with open('./data/services/cex_withdraw_list.json') as file:
                from json import load
                okx_withdraw_list = load(file)
        except:
            self.logger_msg(None, None, f"Bad data in cex_withdraw_list.json", 'error')

        try:
            okx_wallet = okx_withdraw_list[self.client.account_name]
        except Exception as error:
            raise SoftwareExceptionWithoutRetry(f'There is no wallet listed for deposit to CEX: {error}')

        info = f"{okx_wallet[:10]}....{okx_wallet[-6:]}"

        deposit_network, deposit_amount = deposit_data
        network_raw_name = OKX_NETWORKS_NAME[deposit_network]
        ccy, network_name = network_raw_name.split('-')
        withdraw_data = await self.get_currencies(ccy)

        networks_raw_data = {item['chain']: {'can_dep': item['canDep'], 'min_dep': item['minDep']}
                             for item in withdraw_data}

        network_data = networks_raw_data[network_raw_name]
        ccy = f"{ccy}.e" if deposit_network in [29, 30] else ccy
        amount = await self.client.get_smart_amount(deposit_amount, token_name=ccy)

        self.logger_msg(*self.client.acc_info, msg=f"Deposit {amount} {ccy} from {network_name} to OKX wallet: {info}")

        if network_data['can_dep']:

            min_dep = float(network_data['min_dep'])

            if amount >= min_dep:

                if ccy != self.client.token:
                    token_contract = self.client.get_contract(TOKENS_PER_CHAIN[self.client.network.name][ccy])
                    decimals = await self.client.get_decimals(ccy)
                    amount_in_wei = self.client.to_wei(amount, decimals)

                    transaction = await token_contract.functions.transfer(
                        self.client.w3.to_checksum_address(okx_wallet),
                        amount_in_wei
                    ).build_transaction(await self.client.prepare_transaction())
                else:
                    amount_in_wei = self.client.to_wei(amount)
                    transaction = (await self.client.prepare_transaction(value=amount_in_wei)) | {
                        'to': self.client.w3.to_checksum_address(okx_wallet),
                        'data': '0x'
                    }

                sub_balances = await self.get_cex_balances(ccy=ccy)

                result = await self.client.send_transaction(transaction)

                await self.wait_deposit_confirmation(amount, sub_balances, ccy=ccy)

                await self.transfer_from_subs(ccy=ccy, amount=amount)

                return result
            else:
                raise SoftwareExceptionWithoutRetry(f"Minimum to deposit: {min_dep} {ccy}")
        else:
            raise SoftwareExceptionWithoutRetry(f"Deposit to {network_name} is not available")

    async def transfer_from_subs(self, ccy, amount: float = None):
        await self.transfer_from_subaccounts(ccy=ccy, amount=amount)

        await sleep(self, 5, 10)

        await self.transfer_from_spot_to_funding(ccy=ccy)
