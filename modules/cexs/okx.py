import hmac
import base64
import asyncio

from hashlib import sha256
from modules import CEX, Logger
from datetime import datetime, timezone

from modules.interfaces import SoftwareExceptionWithoutRetry, SoftwareException, InsufficientBalanceException
from utils.tools import helper, get_wallet_for_deposit
from config import OKX_NETWORKS_NAME, TOKENS_PER_CHAIN, CEX_WRAPPED_ID, TOKENS_PER_CHAIN2


class OKX(CEX, Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)
        CEX.__init__(self, client, "OKX")
        self.network = self.client.network.name

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
        if ccy == 'USDC.e':
            ccy = 'USDC'

        url = 'https://www.okx.cab/api/v5/asset/currencies'

        params = {'ccy': ccy}

        headers = await self.get_headers(f'{url}?ccy={ccy}')

        return await self.make_request(url=url, headers=headers, params=params, module_name='Token info')

    async def get_balance(self, ccy):
        url_balance = f"https://www.okx.cab/api/v5/asset/balances?ccy={ccy}"

        headers = await self.get_headers(request_path=url_balance)
        balance = (await self.make_request(url=url_balance, headers=headers, module_name='Get Account balance'))

        if balance:
            return float(balance[0]['availBal'])
        raise SoftwareExceptionWithoutRetry(f'Your have not enough {ccy} balance on CEX')

    @helper
    async def transfer_from_subaccounts(self, ccy:str = 'ETH', amount:float = None, silent_mode:bool = False):

        if ccy == 'USDC.e':
            ccy = 'USDC'

        if not silent_mode:
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

            sub_balance = await self.make_request(
                url=url_sub_balance, headers=headers,module_name='Get subAccount balance'
            )

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
                await self.make_request(
                    method="POST", url=url_transfer, data=str(body), headers=headers, module_name='SubAccount transfer'
                )

                self.logger_msg(
                    *self.client.acc_info, msg=f"Transfer {amount} {ccy} to main account complete", type_msg='success'
                )
                if not silent_mode:
                    break
        if flag and not silent_mode:
            self.logger_msg(*self.client.acc_info, msg=f'subAccounts balance: 0 {ccy}', type_msg='warning')
        return True

    @helper
    async def transfer_from_spot_to_funding(self, ccy:str = 'ETH'):

        await asyncio.sleep(5)

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
        else:
            balances['Main CEX Account'] = 0

        for sub_data in sub_list:
            sub_name = sub_data['subAcct']

            url_sub_balance = f"https://www.okx.cab/api/v5/asset/subaccount/balances?subAcct={sub_name}&ccy={ccy}"
            headers = await self.get_headers(request_path=url_sub_balance)

            sub_balance = (await self.make_request(url=url_sub_balance, headers=headers,
                                                   module_name='Get subAccount balance'))
            await asyncio.sleep(3)

            if sub_balance:
                balances[sub_name] = float(sub_balance[0]['availBal'])
            else:
                balances[sub_name] = 0

        return balances

    async def wait_deposit_confirmation(
            self, amount:float, old_sub_balances:dict, ccy:str = 'ETH', check_time:int = 45
    ):

        if ccy == 'USDC.e':
            ccy = 'USDC'

        self.logger_msg(*self.client.acc_info, msg=f"Start checking CEX balances")

        await asyncio.sleep(10)
        while True:
            new_sub_balances = await self.get_cex_balances(ccy=ccy)
            for sub_name, sub_balance in new_sub_balances.items():

                if sub_balance > old_sub_balances[sub_name]:
                    self.logger_msg(*self.client.acc_info, msg=f"Deposit {amount} {ccy} complete", type_msg='success')
                    return True
                else:
                    continue
            else:
                self.logger_msg(*self.client.acc_info, msg=f"Deposit still in progress...", type_msg='warning')
                await asyncio.sleep(check_time)

    async def withdraw(self, withdraw_data:tuple = None):
        url = 'https://www.okx.cab/api/v5/asset/withdrawal'

        network, amount = withdraw_data
        network_raw_name = OKX_NETWORKS_NAME[network]
        split_network_data = network_raw_name.split('-')
        ccy, network_name = split_network_data[0], '-'.join(split_network_data[1:])
        dst_chain_id = CEX_WRAPPED_ID[network]

        await self.transfer_from_subs(ccy=ccy, silent_mode=True)

        if isinstance(amount, str):
            amount = round(await self.get_balance(ccy=ccy) * float(amount), 6)
        else:
            amount = self.client.round_amount(*amount)

        self.logger_msg(*self.client.acc_info, msg=f"Withdraw {amount} {ccy} to {network_name}")

        while True:
            withdraw_raw_data = await self.get_currencies(ccy)
            network_data = {
                item['chain']: {
                    'can_withdraw': item['canWd'],
                    'min_fee': item['minFee'],
                    'min_wd': item['minWd'],
                    'max_wd': item['maxWd']
                } for item in withdraw_raw_data
            }[network_raw_name]

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

                    omnicheck = False
                    if ccy in ['USDV', 'STG']:
                        omnicheck = True

                    old_balance_on_dst = await self.client.wait_for_receiving(
                        dst_chain_id, token_name=ccy, omnicheck=omnicheck, check_balance_on_dst=True
                    )

                    await self.make_request(
                        method='POST', url=url, data=str(body), headers=headers, module_name='Withdraw')

                    self.logger_msg(
                        *self.client.acc_info,
                        msg=f"Withdraw complete. Note: wait a little for receiving funds", type_msg='success'
                    )

                    await self.client.wait_for_receiving(
                        dst_chain_id, old_balance_on_dst, omnicheck=omnicheck, token_name=ccy
                    )

                    return True
                else:
                    raise SoftwareExceptionWithoutRetry(f"Limit range for withdraw: {min_wd:.5f} {ccy} - {max_wd} {ccy}")
            else:
                self.logger_msg(
                    *self.client.acc_info,
                    msg=f"Withdraw from {network_name} is not active now. Will try again in 1 min...",
                    type_msg='warning'
                )
                await asyncio.sleep(60)

    async def deposit(self, deposit_data:tuple = None):
        cex_wallet = get_wallet_for_deposit(self)
        info = f"{cex_wallet[:10]}....{cex_wallet[-6:]}"
        deposit_network, amount = deposit_data
        network_raw_name = OKX_NETWORKS_NAME[deposit_network]
        split_network_data = network_raw_name.split('-')
        ccy, network_name = split_network_data[0], '-'.join(split_network_data[1:])
        if deposit_network in [29, 30]:
            ccy = f"{ccy}.e"

        omnicheck = False
        if ccy in ['USDV', 'STG']:
            omnicheck = True

        self.logger_msg(*self.client.acc_info, msg=f"Deposit {amount} {ccy} from {network_name} to OKX wallet: {info}")

        while True:
            try:
                withdraw_data = await self.get_currencies(ccy)
                network_data = {item['chain']: {'can_dep': item['canDep'], 'min_dep': item['minDep']}
                                for item in withdraw_data}[network_raw_name]

                if network_data['can_dep']:

                    min_dep = float(network_data['min_dep'])

                    if amount >= min_dep:

                        if ccy != self.client.token:
                            if omnicheck:
                                token_contract = self.client.get_contract(TOKENS_PER_CHAIN2[self.network][ccy])
                            else:
                                token_contract = self.client.get_contract(TOKENS_PER_CHAIN[self.network][ccy])
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
                        raise SoftwareExceptionWithoutRetry(f"Minimum to deposit: {min_dep} {ccy}")
                else:
                    self.logger_msg(
                        *self.client.acc_info,
                        msg=f"Deposit to {network_name} is not active now. Will try again in 1 min...",
                        type_msg='warning'
                    )
                    await asyncio.sleep(60)
            except InsufficientBalanceException:
                continue

    async def transfer_from_subs(self, ccy, amount: float = None, silent_mode:bool = False):
        await self.transfer_from_subaccounts(ccy=ccy, amount=amount, silent_mode=silent_mode)

        await self.transfer_from_spot_to_funding(ccy=ccy)
