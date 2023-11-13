import io
import msoffcrypto
import json
import random
import asyncio
import functools
import pandas as pd
from utils.networks import *
from web3 import AsyncWeb3, AsyncHTTPProvider
from termcolor import cprint
from settings import (
    SLEEP_TIME,
    SLEEP_TIME_RETRY,
    MAXIMUM_RETRY,
    GAS_CONTROL,
    MAXIMUM_GWEI,
    SLEEP_TIME_GAS,
    EXCEL_PASSWORD
)


async def sleep(self, min_time=SLEEP_TIME[0], max_time=SLEEP_TIME[1]):
    duration = random.randint(min_time, max_time)
    print()
    self.client.logger.info(f"{self.client.info} {self.__class__.__name__} | 💤 Sleeping for {duration} seconds.")

    await asyncio.sleep(duration)


def get_accounts_data():
    try:
        decrypted_data = io.BytesIO()
        with open('./data/accounts_data.xlsx', 'rb') as file:
            office_file = msoffcrypto.OfficeFile(file)
            office_file.load_key(password=EXCEL_PASSWORD)
            office_file.decrypt(decrypted_data)
            wb = pd.read_excel(decrypted_data)

            accounts_data = {}
            for index, row in wb.iterrows():
                account_name = row["Name"]
                private_key = row["Private Key"]
                proxy = row["Proxy"]
                okx_address = row['OKX address']
                accounts_data[int(index) + 1] = {
                    "account_number": account_name,
                    "private_key": private_key,
                    "proxy": proxy,
                    "okx_wallet": okx_address
                }

            acc_name, priv_key, proxy, okx_wallet = [], [], [], []
            for k, v in accounts_data.items():
                acc_name.append(v['account_number']), priv_key.append(v['private_key'])
                proxy.append(v['proxy']), okx_wallet.append(v['okx_wallet'])

            return acc_name, priv_key, proxy, okx_wallet
    except:
        cprint('\n⚠️⚠️⚠️SET PASSWORD ON YOUR EXCEL FILE!⚠️⚠️⚠️\n', color='light_red', attrs=["blink"])


def create_okx_withdrawal_list():
    okx_data = {}
    w3 = AsyncWeb3()
    _, wallets, _, okx_wallets = get_accounts_data()

    if wallets and okx_wallets:
        with open('./data/services/okx_withdraw_list.json', 'w') as file:
            for private_key, okx_wallet in zip(wallets, okx_wallets):
                okx_data[w3.eth.account.from_key(private_key).address] = okx_wallet
            json.dump(okx_data, file, indent=4)
        cprint('✅ Successfully added and saved OKX wallets data', 'light_blue')
        cprint('⚠️ Check all OKX deposit wallets by yourself to avoid problems', 'light_yellow', attrs=["blink"])
    else:
        cprint('❌ Put your wallets into files, before running this function', 'light_red')


def repeater(func):
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        attempts = 0
        while True:
            try:
                return await func(self, *args, **kwargs)
            except Exception as error:

                await asyncio.sleep(1)
                self.client.logger.error(
                    f"{self.client.info} {error} | Try[{attempts + 1}/{MAXIMUM_RETRY + 1}]")
                await asyncio.sleep(1)

                attempts += 1
                if attempts > MAXIMUM_RETRY:
                    break

                await sleep(self, SLEEP_TIME_RETRY, SLEEP_TIME_RETRY)
        self.client.logger.error(f"{self.client.info} Tries are over, launching next module.\n")
        return False
    return wrapper


def gas_checker(func):
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        if GAS_CONTROL:
            await asyncio.sleep(1)
            print()
            self.client.logger.info(f"{self.client.info} Checking for gas price")
            w3 = AsyncWeb3(AsyncHTTPProvider(random.choice(Ethereum.rpc), request_kwargs=self.client.request_kwargs))
            while True:
                gas = round(AsyncWeb3.from_wei(await w3.eth.gas_price, 'gwei'), 3)
                if gas < MAXIMUM_GWEI:
                    await asyncio.sleep(1)
                    self.client.logger.success(f"{self.client.info} {gas} Gwei | Gas price is good")
                    await asyncio.sleep(1)
                    return await func(self, *args, **kwargs)
                else:
                    await asyncio.sleep(1)
                    self.client.logger.warning(
                        f"{self.client.info} {gas} Gwei | Gas is too high."
                        f" Next check in {SLEEP_TIME_GAS} second")
                    await asyncio.sleep(SLEEP_TIME_GAS)
        return await func(self, *args, **kwargs)
    return wrapper
