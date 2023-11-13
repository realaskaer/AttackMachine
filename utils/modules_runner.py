import json
import random
import asyncio
import telebot
from aiohttp import ClientSession

from modules import Logger
from utils.networks import Ethereum
from web3 import AsyncWeb3, AsyncHTTPProvider
from functions import get_network_by_chain_id
from utils.route_generator import RouteGenerator, AVAILABLE_MODULES_INFO, get_func_by_name
from config import ACCOUNT_NAMES, WALLETS, PROXIES, CHAIN_NAME
from settings import (USE_PROXY, SLEEP_MODE, SLEEP_TIME, SOFTWARE_MODE, HELP_NEW_MODULE, TG_ID, TG_TOKEN, MOBILE_PROXY,
                      MOBILE_PROXY_URL_CHANGER, WALLETS_TO_WORK, TELEGRAM_NOTIFICATIONS, GLOBAL_NETWORK,
                      SAVE_PROGRESS)


class Runner(Logger):
    @staticmethod
    def get_wallets():
        if WALLETS_TO_WORK == 0:
            return zip(ACCOUNT_NAMES, WALLETS)

        elif isinstance(WALLETS_TO_WORK, int):
            return zip(ACCOUNT_NAMES[WALLETS_TO_WORK - 1], WALLETS[WALLETS_TO_WORK - 1])

        elif isinstance(WALLETS_TO_WORK, tuple):
            account_names = [ACCOUNT_NAMES[i-1] for i in WALLETS_TO_WORK]
            accounts = [WALLETS[i-1] for i in WALLETS_TO_WORK]
            return zip(account_names, accounts)

        elif isinstance(WALLETS_TO_WORK, list):
            range_count = range(WALLETS_TO_WORK[0], WALLETS_TO_WORK[1])
            account_names = [ACCOUNT_NAMES[i - 1] for i in range_count]
            accounts = [WALLETS[i - 1] for i in range_count]
            return zip(account_names, accounts)

    @staticmethod
    async def make_request(method:str = 'GET', url:str = None, headers:dict = None):

        async with ClientSession() as session:
            async with session.request(method=method, url=url, headers=headers) as response:

                if response.status == 200:
                    return True
                return False

    @staticmethod
    def load_routes():
        with open('./data/services/wallets_progress.json', 'r') as f:
            return json.load(f)

    async def send_tg_message(self, account_name, private_key, message_to_send, disable_notification=False):
        try:
            await asyncio.sleep(1)
            str_send = '\n'.join(message_to_send)
            bot = telebot.TeleBot(TG_TOKEN)
            bot.send_message(TG_ID, str_send, parse_mode='html', disable_notification=disable_notification)
            print()
            self.logger_msg(account_name, private_key, f"Telegram message sent", 'success')
        except Exception as error:
            self.logger_msg(account_name, private_key, f"Telegram | API Error: {error}", 'error')

    def update_step(self, wallet, step):
        wallets = self.load_routes()
        wallets[wallet]["current_step"] = step
        with open('./data/services/wallets_progress.json', 'w') as f:
            json.dump(wallets, f, indent=4)

    @staticmethod
    async def prepare_update_cell_data(route_generator, result_list, account_name, private_key):
        wallets_list = route_generator.get_wallet_list()
        modules_list = route_generator.get_modules_list()
        address = AsyncWeb3().eth.account.from_key(private_key).address
        for result in result_list:
            wallet_row = wallets_list.index(address) + 2
            module_col = modules_list.index(result[1]) + 3
            if result[0]:
                result_type = 'Done'
            else:
                result_type = 'Error'
            await route_generator.update_cell(account_name, private_key, wallet_row, module_col,
                                              result_type, AVAILABLE_MODULES_INFO[result[1]][2])

    async def check_proxies_status(self):
        tasks = []
        for proxy in PROXIES:
            tasks.append(self.check_proxy_status(None, None, proxy))
        await asyncio.gather(*tasks)

    async def check_proxy_status(self, account_name:str = None, private_key:str = None,
                                 proxy: str = None, silence: bool = False):
        try:
            w3 = AsyncWeb3(AsyncHTTPProvider(random.choice(Ethereum.rpc), request_kwargs={"proxy": f"http://{proxy}"}))
            if await w3.is_connected():
                if not silence:
                    info = f'Proxy {proxy[proxy.find("@"):]} successfully connected to Ethereum RPC'
                    self.logger_msg(account_name, private_key, info, 'success')
                return True
            self.logger_msg(account_name, private_key,f"Proxy: {proxy} can`t connect to Ethereum RPC", 'error')
            return False
        except Exception as error:
            self.logger_msg(account_name, private_key, f"Bad proxy: {proxy} | Error: {error}", 'error')
            return False

    async def get_proxy_for_account(self, account_name, private_key):
        if USE_PROXY:
            try:
                account_number = ACCOUNT_NAMES.index(account_name) + 1
                num_proxies = len(PROXIES)
                proxy = PROXIES[account_number % num_proxies]
                for i in range(num_proxies):
                    if await self.check_proxy_status(account_name, private_key, proxy):
                        return PROXIES[account_number % num_proxies]
                    account_number += 1
                raise RuntimeError("all proxies are BAD!")
            except Exception as error:
                self.logger_msg(account_name, private_key,
                                f"Bad data in proxy, but you want proxy! Error: {error}", 'error')
                raise RuntimeError("Proxy error")

    async def sleep(self, account_number, private_key):
        if SLEEP_MODE:
            duration = random.randint(*SLEEP_TIME)
            self.logger_msg(account_number, private_key, f"💤 Sleeping for {duration} seconds.")
            await asyncio.sleep(duration)

    async def run_module(self, module):
        for account_name, private_key in self.get_wallets():
            proxy = await self.get_proxy_for_account(account_name, private_key)
            module_func = get_func_by_name(module)
            await module_func(account_name, private_key, get_network_by_chain_id(GLOBAL_NETWORK), proxy)
            await self.sleep(account_name, private_key)

    async def run_account_modules(self, account_name, private_key, network, proxy, smart_route, route_generator):
        message_list = []
        result_list = []

        if smart_route:
            try:
                await route_generator.get_smart_route(private_key)
            except Exception as error:
                self.logger_msg(account_name, private_key,f"Can`t generate smart route. Error: {error}", 'error')
                return
        try:
            route:list = self.load_routes()[private_key]['route']
        except Exception as error:
            self.logger_msg(None, None, f"Generate route first!", 'error')
            raise RuntimeError(f"{error}")

        current_step = 0

        if SAVE_PROGRESS:
            current_step = self.load_routes()[private_key]["current_step"]

        await self.sleep(account_name, private_key)

        module_info = AVAILABLE_MODULES_INFO

        info = CHAIN_NAME[GLOBAL_NETWORK]
        message_list.append(f'⚔️ {info}  |  Account name: "{account_name}"\n\n {len(route)} module(s) in route.\n')
        total_info, type_msg = f"All steps in route completed!", 'success'

        while current_step < len(route):
            module_func = get_func_by_name(route[current_step])
            self.logger_msg(account_name, private_key, f"🚀 Launch module: {module_info[module_func][2]}.")
            result = await module_func(account_name, private_key, network, proxy)

            if result:
                self.update_step(private_key, current_step + 1)
                current_step += 1
            else:
                if smart_route and HELP_NEW_MODULE:
                    module_for_help = random.choice(list(AVAILABLE_MODULES_INFO.values())[5:-2])[0]
                    module_name = get_func_by_name(module_for_help.__name__, help_message=True)
                    info = f"Adding new module in route. Module name: {module_name}"
                    await asyncio.sleep(1)
                    self.logger_msg(account_name, private_key, info, 'warning')
                    route.remove(module_func.__name__)
                    route.append(module_for_help.__name__)
                    await asyncio.sleep(2)
                else:
                    message_list.append(f'❌   {AVAILABLE_MODULES_INFO[module_func][2]}\n')
                    result_list.append((False, module_func))
                    total_info, type_msg = f"Some problems during the process of route\n", 'error'
                    break

            message_list.append(f'{"✅" if result else "❌"}   {AVAILABLE_MODULES_INFO[module_func][2]}\n')
            result_list.append((result, module_func))
            await self.sleep(account_name, private_key)

        if smart_route:
            await asyncio.sleep(1)
            await self.prepare_update_cell_data(route_generator, result_list, account_name, private_key)
            await asyncio.sleep(1)

        success_count = len([1 for i in result_list if i[0]])
        errors_count = len(result_list) - success_count
        message_list.append(f'Total result:    ✅ - {success_count}    |    ❌ - {errors_count}')

        if TELEGRAM_NOTIFICATIONS:
            if errors_count > 0:
                disable_notification = True
            else:
                disable_notification = False
            await self.send_tg_message(account_name, private_key, message_to_send=message_list,
                                       disable_notification=disable_notification)
            await asyncio.sleep(1)

        self.logger_msg(account_name, private_key, total_info, type_msg)
        await asyncio.sleep(1)
        self.logger_msg(None, None,f"Start running next wallet!\n", 'success')

    async def run_parallel(self, smart_route, route_generator):
        tasks = []
        for account_name, private_key in self.get_wallets():
            tasks.append(asyncio.create_task(
                self.run_account_modules(
                    account_name, private_key, get_network_by_chain_id(GLOBAL_NETWORK),
                    await self.get_proxy_for_account(account_name, private_key), smart_route, route_generator)))

        await asyncio.gather(*tasks)

    async def run_consistently(self, smart_route, route_generator):
        for account_name, private_key in self.get_wallets():
            await self.run_account_modules(account_name, private_key, get_network_by_chain_id(GLOBAL_NETWORK),
                                           await self.get_proxy_for_account(account_name, private_key),
                                           smart_route, route_generator)

            if MOBILE_PROXY:
                try:
                    if await self.make_request(url=MOBILE_PROXY_URL_CHANGER[0]):
                        self.logger_msg(None, None, f'IP address changed!\n', 'success')
                    else:
                        await self.make_request(url=MOBILE_PROXY_URL_CHANGER[random.randint(1, 2)])
                except Exception as error:
                    self.logger_msg(None, None, f'Bad URL for change IP. Error: {error}', 'error')

        self.logger_msg(None, None, f"All accounts completed their tasks!\n",
                        'success')

    async def run_accounts(self, smart_route: bool):
        route_generator = None
        if smart_route:
            route_generator = RouteGenerator(silent=False)

        if SOFTWARE_MODE:
            await self.run_parallel(smart_route, route_generator)
        else:
            await self.run_consistently(smart_route, route_generator)
