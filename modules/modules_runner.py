import json
import random
import asyncio
from sys import stderr
from loguru import logger
from web3 import AsyncWeb3
from utils.networks import zkSyncEra
from termcolor import cprint
from itertools import zip_longest
from functions import MODULES
from config import WALLETS, PROXIES
from settings import USE_PROXY, SLEEP_MODE, MAX_SLEEP, MIN_SLEEP, SOFTWARE_MODE


def load_routes():
    with open('./data/wallets.json', 'r') as f:
        return json.load(f)


def get_account_data(account_data):
    if USE_PROXY:
        return account_data
    return account_data[0], None


def update_step(wallet, step):

    wallets = load_routes()
    wallets[wallet]["current_step"] = step

    with open('./data/wallets.json', 'w') as f:
        json.dump(wallets, f, indent=4)


async def sleep(account_number, private_key, min_time=MIN_SLEEP, max_time=MAX_SLEEP):
    if SLEEP_MODE:
        address = AsyncWeb3().eth.account.from_key(private_key).address
        address_info = f'{address[:10]}....{address[-6:]}'
        logger.remove()
        logger.add(stderr,
                   format="<white>{time:HH:mm:ss}</white> | <level>" "{level: <8}</level> | <level>{message}</level>")
        duration = random.randint(min_time, max_time)
        logger.info(f"[{account_number}] {address_info} | 💤 Sleeping for {duration} seconds.")
        await asyncio.sleep(duration)


async def run_module(module):
    for num, account in enumerate(zip_longest(WALLETS, PROXIES, fillvalue=None), 1):
        if USE_PROXY:
            wallet, proxy = account
        else:
            wallet, proxy = account[0], None
        print()
        await MODULES[module](num, wallet, zkSyncEra, proxy)


async def run_account_modules(account_number, private_key, network, proxy):

    route = load_routes()[private_key]['route']
    current_step = load_routes()[private_key]["current_step"]
    await sleep(account_number, private_key)

    while current_step < len(route):
        module_name = route[current_step]

        await asyncio.sleep(1)
        cprint(f"\n🚀 Running {module_name} for wallet #{account_number}...", 'light_yellow')
        await MODULES[module_name](account_number, private_key, network, proxy)

        update_step(private_key, current_step + 1)
        current_step += 1

        await sleep(account_number, private_key)

        await asyncio.sleep(1)

    await asyncio.sleep(1)
    cprint(f"\n✅ All steps in route completed!", 'light_green')
    await asyncio.sleep(1)

    await sleep(account_number, private_key)

    cprint(f"\n🔁 Started running next wallet!\n", 'light_green')
    await asyncio.sleep(1)


async def run_parallel():
    tasks = []

    for account_number, account_data in enumerate(zip_longest(WALLETS, PROXIES, fillvalue=None), 1):

        private_key, proxy = get_account_data(account_data)

        task = asyncio.create_task(run_account_modules(account_number, private_key, zkSyncEra, proxy))
        tasks.append(task)

    await asyncio.gather(*tasks)


async def run_consistently():
    for account_number, account_data in enumerate(zip_longest(WALLETS, PROXIES, fillvalue=None), 1):

        private_key, proxy = get_account_data(account_data)

        await run_account_modules(account_number, private_key, zkSyncEra, proxy)

    cprint(f"\n✅ All accounts completed their tasks!\n", 'light_green')


async def run_accounts():
    if SOFTWARE_MODE:
        await run_parallel()
    else:
        await run_consistently()
