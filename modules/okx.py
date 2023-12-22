import hmac
import base64
import asyncio

from hashlib import sha256
from modules import CEX, Logger
from datetime import datetime, timezone
from utils.tools import helper, sleep
from config import OKX_NETWORKS_NAME, TOKENS_PER_CHAIN, OKX_WRAPED_ID, TOKENS_PER_CHAIN2
from settings import (
    OKX_WITHDRAW_NETWORK,
    OKX_WITHDRAW_AMOUNT,
    OKX_DEPOSIT_NETWORK,
    GLOBAL_NETWORK,
    OKX_DEPOSIT_AMOUNT
)


class OKX(CEX, Logger):
    def __init__(self, client):
        Logger.__init__(self)
        super().__init__(client)

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

    async def get_currencies(self, ccy: str = 'ETH'):
        url = 'https://www.okx.cab/api/v5/asset/currencies'

        params = {'ccy': ccy}

        headers = await self.get_headers(f'{url}?ccy={ccy}')

        return await self.make_request(url=url, headers=headers, params=params, module_name='Token info')

    @helper
    async def withdraw(self, want_balance:float = 0):
        if GLOBAL_NETWORK == 9:
            await self.client.initialize_account(check_balance=True)

        url = 'https://www.okx.cab/api/v5/asset/withdrawal'

        ccy = OKX_NETWORKS_NAME[OKX_WITHDRAW_NETWORK].split('-')[0]
        withdraw_data = await self.get_currencies(ccy)

        networks_data = {item['chain']: {'can_withdraw': item['canWd'], 'min_fee': item['minFee'],
                                         'min_wd': item['minWd'], 'max_wd': item['maxWd']} for item in withdraw_data}

        network_name = OKX_NETWORKS_NAME[OKX_WITHDRAW_NETWORK]
        network_data = networks_data[network_name]
        if want_balance:
            amount = want_balance
        else:
            amount = await self.client.get_smart_amount(OKX_WITHDRAW_AMOUNT)

        self.logger_msg(
            *self.client.acc_info, msg=f"Withdraw {amount} {ccy} to {network_name[4 if ccy == 'ETH' else 5:]}")

        if network_data['can_withdraw']:
            address = f"0x{hex(self.client.address)[2:]:0>64}" if OKX_WITHDRAW_NETWORK == 5 else self.client.address
            min_wd, max_wd = float(network_data['min_wd']), float(network_data['max_wd'])

            if min_wd <= amount <= max_wd:

                body = {
                    "ccy": ccy,
                    "amt": amount,
                    "dest": "4",
                    "toAddr": address,
                    "fee": network_data['min_fee'],
                    "chain": f"{network_name}",
                }

                headers = await self.get_headers(method="POST", request_path=url, body=str(body))
                dst_chain_id = OKX_WRAPED_ID[OKX_WITHDRAW_NETWORK]

                old_balance_on_dst = await self.client.wait_for_receiving(dst_chain_id,token_name=ccy,
                                                                          check_balance_on_dst=True)

                await self.make_request(method='POST', url=url, data=str(body), headers=headers, module_name='Withdraw')

                self.logger_msg(*self.client.acc_info,
                                msg=f"Withdraw complete. Note: wait a little for receiving funds", type_msg='success')

                await self.client.wait_for_receiving(dst_chain_id, old_balance_on_dst, token_name=ccy)

                return True
            else:
                raise RuntimeError(f"Limit range for withdraw: {min_wd:.5f} {ccy} - {max_wd} {ccy}")
        else:
            raise RuntimeError(f"Withdraw from {network_name} is not available")

    @helper
    async def transfer_from_subaccounts(self):

        self.logger_msg(*self.client.acc_info, msg=f'Checking subAccounts balance')

        url_sub_list = "https://www.okx.cab/api/v5/users/subaccount/list"

        flag = True
        headers = await self.get_headers(request_path=url_sub_list)
        sub_list = await self.make_request(url=url_sub_list, headers=headers, module_name='Get subAccounts list')
        await asyncio.sleep(1)

        for sub_data in sub_list:
            sub_name = sub_data['subAcct']

            url_sub_balance = f"https://www.okx.cab/api/v5/asset/subaccount/balances?subAcct={sub_name}&ccy=ETH"
            headers = await self.get_headers(request_path=url_sub_balance)

            sub_balance = (await self.make_request(url=url_sub_balance, headers=headers,
                                                   module_name='Get subAccount balance'))[0]['availBal']

            await asyncio.sleep(1)

            if float(sub_balance) != 0.0:
                flag = False
                self.logger_msg(*self.client.acc_info, msg=f'{sub_name} | subAccount balance : {sub_balance} ETH')

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

                self.logger_msg(*self.client.acc_info,
                                msg=f"Transfer {sub_balance} ETH to main account complete",
                                type_msg='success')
        if flag:
            self.logger_msg(*self.client.acc_info, msg=f'subAccounts balance: 0 ETH', type_msg='warning')
        return True

    @helper
    async def transfer_from_spot_to_funding(self):

        url_balance = "https://www.okx.cab/api/v5/account/balance?ccy=ETH"
        headers = await self.get_headers(request_path=url_balance)
        balance = (await self.make_request(url=url_balance, headers=headers,
                                           module_name='Trading account'))[0]["details"]

        for ccy in balance:
            if ccy['ccy'] == 'ETH' and ccy['availBal'] != '0':

                self.logger_msg(*self.client.acc_info, msg=f"Main trading account balance: {ccy['availBal']} ETH")

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
                self.logger_msg(*self.client.acc_info,
                                msg=f"Transfer {float(ccy['availBal']):.6f} ETH to funding account complete",
                                type_msg='success')
                break
            else:
                self.logger_msg(*self.client.acc_info, msg=f"Main trading account balance: 0 ETH", type_msg='warning')
                break

        return True

    async def get_sub_balances(self, ccy:str = 'ETH'):
        sub_balances = {}
        url_sub_list = "https://www.okx.cab/api/v5/users/subaccount/list"

        await asyncio.sleep(10)

        headers = await self.get_headers(request_path=url_sub_list)
        sub_list = await self.make_request(url=url_sub_list, headers=headers, module_name='Get subAccounts list')

        for sub_data in sub_list:
            sub_name = sub_data['subAcct']

            url_sub_balance = f"https://www.okx.cab/api/v5/asset/subaccount/balances?subAcct={sub_name}&ccy={ccy}"
            headers = await self.get_headers(request_path=url_sub_balance)

            sub_balance = (await self.make_request(url=url_sub_balance, headers=headers,
                                                   module_name='Get subAccount balance'))[0]['availBal']

            await asyncio.sleep(3)

            sub_balances[sub_name] = float(sub_balance)

        return sub_balances

    async def wait_deposit_confirmation(self, amount:float, old_sub_balances:dict, ccy:str = 'ETH',
                                        check_time:int = 45, timeout:int = 1200):

        self.logger_msg(*self.client.acc_info, msg=f"Start checking CEX balances")

        await asyncio.sleep(10)
        total_time = 0
        while total_time < timeout:
            new_sub_balances = await self.get_sub_balances(ccy=ccy)
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

        raise RuntimeError(f'Deposit does not complete in {timeout} seconds')

    @helper
    async def deposit(self):
        if GLOBAL_NETWORK == 9:
            await self.client.initialize_account()

        amount = await self.client.get_smart_amount(OKX_DEPOSIT_AMOUNT)
        amount_in_wei = int(amount * 10 ** 18)

        try:
            with open('./data/services/okx_withdraw_list.json') as file:
                from json import load
                okx_withdraw_list = load(file)
        except:
            self.logger_msg(None, None, f"Bad data in okx_wallet_list.json", 'error')

        try:
            okx_wallet = okx_withdraw_list[self.client.account_name]
        except Exception as error:
            raise RuntimeError(f'There is no wallet listed for deposit to OKX: {error}')

        info = f"{okx_wallet[:10]}....{okx_wallet[-6:]}"
        network_name = self.client.network.name
        ccy = OKX_NETWORKS_NAME[OKX_DEPOSIT_NETWORK].split('-')[0]

        self.logger_msg(*self.client.acc_info, msg=f"Deposit {amount} {ccy} from {network_name} to OKX wallet: {info}")

        withdraw_data = await self.get_currencies(ccy)

        networks_data = {item['chain']: {'can_dep': item['canDep'], 'min_dep': item['minDep']}
                         for item in withdraw_data}

        network_name = OKX_NETWORKS_NAME[OKX_DEPOSIT_NETWORK]
        network_data = networks_data[network_name]

        if network_data['can_dep']:

            min_dep = float(network_data['min_dep'])

            if amount >= min_dep:

                if self.client.network.name == 'Starknet':
                    await self.client.initialize_account()
                    transaction = self.client.prepare_call(
                        contract_address=TOKENS_PER_CHAIN['Starknet'][ccy],
                        selector_name="transfer",
                        calldata=[
                            int(okx_wallet, 16),
                            amount_in_wei, 0
                        ]
                    )
                else:
                    if ccy in ['USDT', 'USDC']:
                        token_contract = self.client.get_contract(TOKENS_PER_CHAIN2[self.client.network.name][ccy])
                        transaction = await token_contract.functions.transfer(
                            self.client.w3.to_checksum_address(okx_wallet),
                            amount_in_wei
                        ).build_transaction(await self.client.prepare_transaction())
                    else:
                        transaction = (await self.client.prepare_transaction(value=int(amount_in_wei))) | {
                            'to': self.client.w3.to_checksum_address(okx_wallet),
                            'data': '0x'
                        }

                sub_balances = await self.get_sub_balances()

                result = await self.client.send_transaction(transaction)

                await self.wait_deposit_confirmation(amount, sub_balances)

                return result
            else:
                raise RuntimeError(f"Minimum to deposit: {min_dep} {ccy}")
        else:
            raise RuntimeError(f"Deposit to {network_name} is not available")

    @helper
    async def collect_from_sub(self):

        await self.transfer_from_subaccounts()

        await sleep(self, 5, 10)

        await self.transfer_from_spot_to_funding()

        return True
