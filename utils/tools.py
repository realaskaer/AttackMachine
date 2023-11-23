import io
import json
import random
import asyncio
import functools
import msoffcrypto
import pandas as pd
from getpass import getpass
from utils.networks import *
from termcolor import cprint
from datetime import datetime, timedelta
from web3 import AsyncWeb3, AsyncHTTPProvider
from msoffcrypto.exceptions import DecryptionError, InvalidKeyError
from settings import (
    SLEEP_TIME,
    GLOBAL_NETWORK,
    SLEEP_TIME_RETRY,
    MAXIMUM_RETRY,
    GAS_CONTROL,
    MAXIMUM_GWEI,
    SLEEP_TIME_GAS,
    EXCEL_PASSWORD,
    CONTROL_TIMES_FOR_SLEEP,
    ACCOUNTS_IN_STREAM,
    SOFTWARE_MODE,
    EXCEL_PAGE_NAME, SLEEP_TIME_STREAM
)


async def sleep(self, min_time=SLEEP_TIME[0], max_time=SLEEP_TIME[1]):
    duration = random.randint(min_time, max_time)
    print()
    self.client.logger_msg(self.client.account_name, self.client.private_key,
                           f"{self.__class__.__name__} | 💤 Sleeping for {duration} seconds.")
    await asyncio.sleep(duration)


def get_accounts_data():
    decrypted_data = io.BytesIO()
    with open('./data/accounts_data.xlsx', 'rb') as file:
        if EXCEL_PASSWORD:
            cprint('⚔️ Enter the password degen', color='light_blue')
            password = getpass()
            office_file = msoffcrypto.OfficeFile(file)

            try:
                office_file.load_key(password=password)
            except msoffcrypto.exceptions.DecryptionError:
                cprint('\n⚠️ Incorrect password to decrypt Excel file! ⚠️\n', color='light_red', attrs=["blink"])
                raise DecryptionError('Incorrect password')

            try:
                office_file.decrypt(decrypted_data)
            except msoffcrypto.exceptions.InvalidKeyError:
                cprint('\n⚠️ Incorrect password to decrypt Excel file! ⚠️\n', color='light_red', attrs=["blink"])
                raise InvalidKeyError('Incorrect password')

            except msoffcrypto.exceptions.DecryptionError:
                cprint('\n⚠️ Set password on your Excel file first! ⚠️\n', color='light_red', attrs=["blink"])
                raise DecryptionError('Excel without password')

            office_file.decrypt(decrypted_data)

            try:
                wb = pd.read_excel(decrypted_data, sheet_name=EXCEL_PAGE_NAME)
            except ValueError as error:
                cprint('\n⚠️ Wrong page name! ⚠️\n', color='light_red', attrs=["blink"])
                raise ValueError(f"{error}")
        else:
            try:
                wb = pd.read_excel(file, sheet_name=EXCEL_PAGE_NAME)
            except ValueError as error:
                cprint('\n⚠️ Wrong page name! ⚠️\n', color='light_red', attrs=["blink"])
                raise ValueError(f"{error}")

        accounts_data = {}
        for index, row in wb.iterrows():
            account_name = row["Name"]
            private_key = row["Private Key"]
            private_key_evm = row["Private Key EVM"] if GLOBAL_NETWORK == 9 else 0x123
            proxy = row["Proxy"]
            okx_address = row['OKX address']
            accounts_data[int(index) + 1] = {
                "account_number": account_name,
                "private_key_evm": private_key_evm,
                "private_key": private_key,
                "proxy": proxy,
                "okx_wallet": okx_address,
            }

        acc_name, priv_key_evm, priv_key, proxy, okx_wallet = [], [], [], [], []
        for k, v in accounts_data.items():
            acc_name.append(v['account_number'])
            priv_key_evm.append(v['private_key_evm'])
            priv_key.append(v['private_key'])
            proxy.append(v['proxy'] if isinstance(v['proxy'], str) else None)
            okx_wallet.append(v['okx_wallet'] if isinstance(v['okx_wallet'], str) else None)

        proxy = [item for item in proxy if item is not None]
        okx_wallet = [item for item in okx_wallet if item is not None]

        return acc_name, priv_key_evm, priv_key, proxy, okx_wallet


def clean_stark_file():
    with open('./data/services/stark_data.json', 'w') as file:
        file.truncate(0)


def drop_date():
    current_date = datetime.now()
    random_months = random.randint(1, 4)

    future_date = current_date + timedelta(days=random_months * 30)

    return future_date.strftime("%Y.%m.%d")


def create_okx_withdrawal_list():
    from config import ACCOUNT_NAMES, OKX_WALLETS
    okx_data = {}
    w3 = AsyncWeb3()

    if ACCOUNT_NAMES and OKX_WALLETS:
        with open('./data/services/okx_withdraw_list.json', 'w') as file:
            for account_name, okx_wallet in zip(ACCOUNT_NAMES, OKX_WALLETS):
                okx_data[account_name] = okx_wallet
            json.dump(okx_data, file, indent=4)
        cprint('✅ Successfully added and saved OKX wallets data', 'light_blue')
        cprint('⚠️ Check all OKX deposit wallets by yourself to avoid problems', 'light_yellow', attrs=["blink"])
    else:
        cprint('❌ Put your wallets into files, before running this function', 'light_red')


def repeater(func):
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        attempts = 0
        account_data = self.client.account_name, self.client.private_key

        while True:
            try:
                return await func(self, *args, **kwargs)
            except Exception as error:

                await asyncio.sleep(1)
                self.client.logger_msg(
                    *account_data, f"{error} | Try[{attempts + 1}/{MAXIMUM_RETRY + 1}]", 'error')
                await asyncio.sleep(1)

                attempts += 1
                if attempts > MAXIMUM_RETRY:
                    break

                await sleep(self, *SLEEP_TIME_RETRY)
        self.client.logger_msg(*account_data, f"Tries are over, launching next module.\n", 'error')
        return False
    return wrapper


def gas_checker(func):
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        if GAS_CONTROL:
            await asyncio.sleep(1)
            print()
            flag = False
            counter = 0
            account_data = self.client.account_name, self.client.private_key

            self.client.logger_msg(*account_data, f"Checking for gas price")

            w3 = None
            if self.client.network.name != "Starknet":
                w3 = AsyncWeb3(AsyncHTTPProvider(random.choice(Ethereum.rpc),
                                                 request_kwargs=self.client.request_kwargs))
            while True:
                if self.client.network.name == "Starknet":
                    gas = float(f"{(await self.client.get_gas_price()):.2f}")
                else:
                    gas = round(AsyncWeb3.from_wei(await w3.eth.gas_price, 'gwei'), 3)
                if gas < MAXIMUM_GWEI:
                    await asyncio.sleep(1)
                    self.client.logger_msg(*account_data, f"{gas} Gwei | Gas price is good", 'success')
                    await asyncio.sleep(1)
                    if flag and counter == CONTROL_TIMES_FOR_SLEEP and SOFTWARE_MODE:
                        account_number = random.randint(1, ACCOUNTS_IN_STREAM)
                        sleep_duration = tuple(x * account_number for x in SLEEP_TIME_STREAM)
                        await sleep(self, *sleep_duration)
                    return await func(self, *args, **kwargs)
                else:
                    flag = True
                    counter += 1
                    await asyncio.sleep(1)
                    self.client.logger_msg(
                        *account_data, f"{gas} Gwei | Gas is too high. Next check in {SLEEP_TIME_GAS} second")
                    await asyncio.sleep(SLEEP_TIME_GAS)
        return await func(self, *args, **kwargs)
    return wrapper
