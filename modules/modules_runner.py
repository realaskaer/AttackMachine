import json
import random
import asyncio
from sys import stderr
from loguru import logger
from web3 import AsyncWeb3
from utils.networks import ScrollRPC
from termcolor import cprint
from functions import MODULES
from config import WALLETS, PROXIES
from settings import USE_PROXY, SLEEP_MODE, MAX_SLEEP, MIN_SLEEP, SOFTWARE_MODE, WALLETS_TO_WORK


def get_wallets():
    if WALLETS_TO_WORK == 0:
        return WALLETS
    elif isinstance(WALLETS_TO_WORK, int):
        return [WALLETS[WALLETS_TO_WORK-1]]
    elif isinstance(WALLETS_TO_WORK, tuple):
        return [WALLETS[i-1] for i in WALLETS_TO_WORK]
    elif isinstance(WALLETS_TO_WORK, list):
        return [WALLETS[i-1] for i in range(WALLETS_TO_WORK[0], WALLETS_TO_WORK[1])]


def load_routes():
    with open('./data/wallets.json', 'r') as f:
        return json.load(f)


def update_step(wallet, step):
    wallets = load_routes()
    wallets[wallet]["current_step"] = step
    with open('./data/wallets.json', 'w') as f:
        json.dump(wallets, f, indent=4)


async def get_proxy_for_account(account_number):
    if USE_PROXY:
        try:
            num_proxies = len(PROXIES)
            return PROXIES[account_number % num_proxies]
        except:
            cprint(f"\n❌ Nothing in proxy.txt, but you want proxy!\n", 'light_red')
            return None


async def sleep(account_number, private_key):
    if SLEEP_MODE:
        address = AsyncWeb3().eth.account.from_key(private_key).address
        address_info = f'{address[:10]}....{address[-6:]}'
        logger.remove()
        logger.add(stderr,
                   format="<cyan>{time:HH:mm:ss}</cyan> | <level>" "{level: <8}</level> | <level>{message}</level>")
        duration = random.randint(MIN_SLEEP, MAX_SLEEP)
        logger.info(f"[{account_number}] {address_info} | 💤 Sleeping for {duration} seconds.")
        await asyncio.sleep(duration)


async def run_module(module):
    for account_number, private_key in enumerate(get_wallets(), 1):
        proxy = await get_proxy_for_account(account_number)
        await MODULES[module](account_number, private_key, ScrollRPC, proxy)
        await sleep(account_number, private_key)


async def run_account_modules(account_number, private_key, network, proxy):
    route = load_routes()[private_key]['route']
    current_step = load_routes()[private_key]["current_step"]

    await sleep(account_number, private_key)

    while current_step < len(route):
        module_name = route[current_step]
        cprint(f"\n🚀 Running {module_name} for wallet #{account_number}...", 'light_yellow')
        await MODULES[module_name](account_number, private_key, network, proxy)

        update_step(private_key, current_step + 1)
        current_step += 1

        await sleep(account_number, private_key)

    cprint(f"\n✅ All steps in route completed!", 'light_green')
    cprint(f"\n🔁 Started running next wallet!\n", 'light_green')


async def run_parallel():
    tasks = []

    for account_number, private_key in enumerate(get_wallets(), 1):
        tasks.append(asyncio.create_task(run_account_modules(account_number, private_key, ScrollRPC,
                                                             await get_proxy_for_account(account_number))))

    await asyncio.gather(*tasks)


async def run_consistently():
    for account_number, private_key in enumerate(get_wallets(), 1):
        await run_account_modules(account_number, private_key, ScrollRPC, await get_proxy_for_account(account_number))
    cprint(f"\n✅ All accounts completed their tasks!\n", 'light_green')


async def run_accounts():
    if SOFTWARE_MODE:
        await run_parallel()
    else:
        await run_consistently()
