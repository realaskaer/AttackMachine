import os
import json

from functions import *
from web3 import AsyncWeb3
from config import WALLETS
from modules import Logger
from gspread import Client, Spreadsheet, Worksheet, service_account
from settings import (GOOGLE_SHEET_URL, GOOGLE_SHEET_PAGE_NAME, MODULES_COUNT, ALL_MODULES_TO_RUN,
                      TRANSFER_IN_ROUTES, TRANSFER_COUNT, EXCLUDED_MODULES,
                      DMAIL_IN_ROUTES, DMAIL_COUNT, COLLATERAL_IN_ROUTES, COLLATERAL_COUNT,
                      CLASSIC_ROUTES_MODULES_USING, WITHDRAW_LP, WITHDRAW_LANDING, DEPOSIT_CONFIG)

GSHEET_CONFIG = "./data/services/service_account.json"
os.environ["GSPREAD_SILENCE_WARNINGS"] = "1"

AVAILABLE_MODULES_INFO = {
    # module_name                       : (module name, priority, tg info)
    okx_withdraw                        : (okx_withdraw, 0, 'OKX Withdraw'),
    bridge_rhino                        : (bridge_rhino, 1, 'Rhino.fi Bridge'),
    bridge_layerswap                    : (bridge_layerswap, 1, 'LayerSwap Bridge'),
    bridge_orbiter                      : (bridge_orbiter, 1, 'Orbiter Bridge'),
    bridge_txsync                       : (bridge_txsync, 1, 'txSync Bridge'),
    add_liquidity_maverick              : (add_liquidity_maverick, 2, 'Maverick Liquidity'),
    add_liquidity_mute                  : (add_liquidity_mute, 2, 'Mute Liquidity'),
    add_liquidity_syncswap              : (add_liquidity_syncswap, 2, 'SyncSwap Liquidity'),
    deposit_basilisk                    : (deposit_basilisk, 2, 'Deposit Basilisk'),
    deposit_eralend                     : (deposit_eralend, 2, 'Deposit EraLend'),
    deposit_reactorfusion               : (deposit_reactorfusion, 2, 'Deposit ReactorFusion'),
    deposit_zerolend                    : (deposit_zerolend, 2, 'Deposit ZeroLend'),
    enable_collateral_basilisk          : (enable_collateral_basilisk, 2, 'Collateral Basilisk'),
    enable_collateral_eralend           : (enable_collateral_eralend, 2, 'Collateral EraLend'),
    enable_collateral_reactorfusion     : (enable_collateral_reactorfusion, 2, 'Collateral ReactorFusion'),
    enable_collateral_zerolend          : (enable_collateral_zerolend, 2, 'Collateral ZeroLend'),
    swap_izumi                          : (swap_izumi, 2, 'Swap iZumi'),
    swap_maverick                       : (swap_maverick, 2, 'Swap Maverick'),
    swap_mute                           : (swap_mute, 2, 'Swap Mute'),
    swap_odos                           : (swap_odos, 2, 'Swap ODOS'),
    swap_oneinch                        : (swap_oneinch, 2, 'Swap 1inch'),
    swap_openocean                      : (swap_openocean, 2, 'Swap OpenOcean'),
    swap_pancake                        : (swap_pancake, 2, 'Swap Pancake'),
    swap_spacefi                        : (swap_spacefi, 2, 'Swap SpaceFi'),
    swap_rango                          : (swap_rango, 2, 'Swap Rango'),
    swap_xyfinance                      : (swap_xyfinance, 2, 'Swap XYfinance'),
    swap_syncswap                       : (swap_syncswap, 2, 'Swap SyncSwap'),
    #swap_velocore                       : (swap_velocore, 2, 'Swap Velocore'),
    swap_vesync                         : (swap_vesync, 2, 'Swap VeSync'),
    swap_woofi                          : (swap_woofi, 2, 'Swap WooFi'),
    swap_zkswap                         : (swap_zkswap, 2, 'Swap zkSwap'),
    wrap_eth                            : (wrap_eth, 2, 'Wrap ETH'),
    disable_collateral_basilisk         : (disable_collateral_basilisk, 3, 'Collateral Basilisk'),
    disable_collateral_eralend          : (disable_collateral_eralend, 3, 'Collateral EraLend'),
    disable_collateral_reactorfusion    : (disable_collateral_reactorfusion, 3, 'Collateral ReactorFusion'),
    disable_collateral_zerolend         : (disable_collateral_zerolend, 3, 'Collateral ZeroLend'),
    create_omnisea                      : (create_omnisea, 3, 'Omnisea Create NFT'),
    create_safe                         : (create_safe, 3, 'Gnosis Safe'),
    mint_and_bridge_l2telegraph         : (mint_and_bridge_l2telegraph, 3, 'L2Telegraph NFT bridge'),
    mint_domain_ens                     : (mint_domain_ens, 3, 'ENS Domain Mint'),
    mint_domain_zns                     : (mint_domain_zns, 3, 'ZNS Domain Mint'),
    mint_mailzero                       : (mint_mailzero, 3, 'MailZero NFT mint'),
    mint_tevaera                        : (mint_tevaera, 3, 'Tevaera ID & NFT mint'),
    mint_zerius                         : (mint_zerius, 3, 'Zerius Mint NFT'),
    deploy_contract                     : (deploy_contract, 3, 'Contract Deploy'),
    bridge_zerius                       : (bridge_zerius, 3, 'Zerius Bridge NFT'),
    refuel_bungee                       : (refuel_bungee, 3, 'Bungee Refuel'),
    refuel_merkly                       : (refuel_merkly, 3, 'Merkly Refuel'),
    send_message_dmail                  : (send_message_dmail, 3, 'Dmail Message'),
    send_message_l2telegraph            : (send_message_l2telegraph, 3, 'L2Telegraph Message'),
    transfer_eth                        : (transfer_eth, 3, 'Transfer ETH'),
    transfer_eth_to_myself              : (transfer_eth_to_myself, 3, 'Transfer ETH to myself'),
    withdraw_liquidity_maverick         : (withdraw_liquidity_maverick, 3, 'Maverick withdraw liquidity'),
    withdraw_liquidity_mute             : (withdraw_liquidity_mute, 3, 'Mute withdraw liquidity'),
    withdraw_liquidity_syncswap         : (withdraw_liquidity_syncswap, 3, 'SyncSwap withdraw liquidity'),
    withdraw_basilisk                   : (withdraw_basilisk, 3, 'Withdraw Basilisk'),
    withdraw_eralend                    : (withdraw_eralend, 3, 'Withdraw EraLend'),
    withdraw_reactorfusion              : (withdraw_reactorfusion, 3, 'Withdraw ReactorFusion'),
    withdraw_zerolend                   : (withdraw_zerolend, 3, 'Withdraw ZeroLend'),
    withdraw_txsync                     : (withdraw_txsync, 3, 'Withdraw txSync'),
    okx_deposit                         : (okx_deposit, 4, 'OKX Deposit'),
    okx_collect_from_sub                : (okx_collect_from_sub, 5, 'OKX Collect money')
}


def get_func_by_name(module_name, help_message:bool = False):
    for k, v in AVAILABLE_MODULES_INFO.items():
        if k.__name__ == module_name:
            if help_message:
                return v[2]
            return v[0]


class RouteGenerator(Logger):
    def __init__(self, silent:bool = True):
        super().__init__()
        if GOOGLE_SHEET_URL != '' and not silent:
            self.gc: Client = service_account(filename=GSHEET_CONFIG)
            self.sh: Spreadsheet = self.gc.open_by_url(GOOGLE_SHEET_URL)
            self.ws: Worksheet = self.sh.worksheet(GOOGLE_SHEET_PAGE_NAME)
        else:
            self.gc, self.sh, self.ws = None, None, None
        self.function_mappings = {
            'Syncswap Liquidity': add_liquidity_syncswap,
            'Maverick Liquidity': add_liquidity_maverick,
            'Mute Liquidity': add_liquidity_mute,
            'Syncswap': swap_syncswap,
            'Mute': swap_mute,
            'Maverick': swap_maverick,
            'iZumi': swap_izumi,
            'Rango': swap_rango,
            'VeSync': swap_vesync,
            'Spacefi': swap_spacefi,
            'Pancake': swap_pancake,
            'Woofi': swap_woofi,
            'Odos': swap_odos,
            'zkSwap': swap_zkswap,
            'XYfinance': swap_xyfinance,
            #'Velocore': swap_velocore,
            '1inch': swap_oneinch,
            'Openocean': swap_openocean,
            'EraLend': deposit_eralend,
            'ZeroLend': deposit_zerolend,
            'Basilisk': deposit_basilisk,
            'Reactorfusion': deposit_reactorfusion,
            'Zerius Mint NFT': mint_zerius,
            'Zerius Bridge NFT': bridge_zerius,
            'Omnisea Create NFT': create_omnisea,
            'Tavaera ID & NFT mint': mint_tevaera,
            'Mailzero NFT mint': mint_mailzero,
            'ZNS Domain Mint': mint_domain_zns,
            'ENS Domain Mint': mint_domain_ens,
            'L2Telegraph NFT bridge': mint_and_bridge_l2telegraph,
            'Gnosis Safe': create_safe,
            'Contract Deploy': deploy_contract,
            'Dmail': send_message_dmail,
            'L2Telegraph message': send_message_l2telegraph,
            'Wrap ETH': wrap_eth,
            'Merkly Refuel': refuel_merkly,
            'Bungee Refuel': refuel_bungee,
            'Withdraw txSync': withdraw_txsync,
        }

    @staticmethod
    def classic_generate_route():
        route = []
        for i in CLASSIC_ROUTES_MODULES_USING:
            module_name = random.choice(i)
            if module_name is None:
                continue
            module = get_func_by_name(module_name)
            route.append(module.__name__)
        return route

    def get_function_mappings_key(self, value):
        for key, val in self.function_mappings.items():
            if val == value:
                return key

    async def update_cell(self, account_name:str, private_key:str, row: int, col: int, value, module_name):
        try:
            self.ws.update_cell(row, col, value)
            if value == 'Done':
                type_msg = 'success'
            else:
                type_msg = 'warning'

            self.logger_msg(account_name, private_key,
                            f'Google Sheet updated! Module name: {module_name}. Result: {value}', type_msg)
        except Exception as error:
            self.logger_msg(account_name, private_key, f'Can`t update Google Sheet Error: {error}', 'error')

    def get_wallet_list(self):
        return self.ws.col_values(2)[1:]

    def get_modules_list(self):
        modules_list_str = self.ws.row_values(1)[2:]

        modules_list = []
        for module in modules_list_str:
            if module in self.function_mappings:
                modules_list.append(self.function_mappings[module])
        return modules_list

    async def get_smart_route(self, private_key: str):
        try:
            wallets_list = self.get_wallet_list()
            modules_list = self.get_modules_list()
        except Exception as error:
            self.logger_msg(None, None, f"Put data into 'GOOGLE_SHEET_URL' and 'service_accounts.json' first!", 'error')
            raise RuntimeError(f"{error}")

        wallet_address = AsyncWeb3().eth.account.from_key(private_key).address

        wallet_modules_statuses = self.ws.row_values(wallets_list.index(wallet_address) + 2)[2:]

        modules_to_work = []

        collaterals_modules = [enable_collateral_eralend, enable_collateral_basilisk,
                               enable_collateral_zerolend, enable_collateral_reactorfusion,
                               disable_collateral_basilisk,disable_collateral_eralend,
                               disable_collateral_reactorfusion,disable_collateral_zerolend]

        for i in range(len(wallet_modules_statuses)):
            if wallet_modules_statuses[i] in ["Not Started", "Error"]:
                modules_to_work.append(modules_list[i])

        possible_modules = [m for m in modules_to_work if m not in
                            [module for module in EXCLUDED_MODULES if module in self.function_mappings]]

        want_count = len(modules_to_work) if ALL_MODULES_TO_RUN else random.choice(MODULES_COUNT)
        possible_count = min(want_count, len(possible_modules))

        possible_modules_data = [AVAILABLE_MODULES_INFO[module] for module in possible_modules]

        smart_route: list = random.sample(possible_modules_data, possible_count)

        if DMAIL_IN_ROUTES:
            smart_route.extend([AVAILABLE_MODULES_INFO[send_message_dmail] for _ in range(random.choice(DMAIL_COUNT))])

        if COLLATERAL_IN_ROUTES:
            smart_route.extend([AVAILABLE_MODULES_INFO[random.choice(collaterals_modules)]
                                for _ in range(random.choice(COLLATERAL_COUNT))])

        if TRANSFER_IN_ROUTES:
            smart_route.extend([AVAILABLE_MODULES_INFO[random.choice([transfer_eth_to_myself, transfer_eth])]
                                for _ in range(random.choice(TRANSFER_COUNT))])

        if WITHDRAW_LP:
            smart_route.append(AVAILABLE_MODULES_INFO[withdraw_liquidity_maverick])
            smart_route.append(AVAILABLE_MODULES_INFO[withdraw_liquidity_mute])
            smart_route.append(AVAILABLE_MODULES_INFO[withdraw_liquidity_syncswap])

        if WITHDRAW_LANDING:
            smart_route.append(AVAILABLE_MODULES_INFO[withdraw_eralend])
            smart_route.append(AVAILABLE_MODULES_INFO[withdraw_reactorfusion])
            smart_route.append(AVAILABLE_MODULES_INFO[withdraw_basilisk])
            smart_route.append(AVAILABLE_MODULES_INFO[withdraw_zerolend])

        bridge_modules = [AVAILABLE_MODULES_INFO[bridge_rhino] if DEPOSIT_CONFIG['bridge_rhino'] else None,
                          AVAILABLE_MODULES_INFO[bridge_layerswap] if DEPOSIT_CONFIG['bridge_layerswap'] else None,
                          AVAILABLE_MODULES_INFO[bridge_orbiter] if DEPOSIT_CONFIG['bridge_orbiter'] else None,
                          AVAILABLE_MODULES_INFO[bridge_txsync] if DEPOSIT_CONFIG['bridge_txsync'] else None]

        smart_route.append(random.choice(bridge_modules))

        smart_route.append(AVAILABLE_MODULES_INFO[okx_withdraw] if DEPOSIT_CONFIG['okx_withdraw'] else None)
        smart_route.append(AVAILABLE_MODULES_INFO[okx_deposit] if DEPOSIT_CONFIG['okx_deposit'] else None)
        smart_route.append(AVAILABLE_MODULES_INFO[okx_collect_from_sub] if DEPOSIT_CONFIG['okx_collect_from_sub']
                           else None)

        random.shuffle(smart_route)

        smart_route_with_priority = [i[0].__name__ for i in sorted(list(filter(None, smart_route)), key=lambda x: x[1])]

        self.routes_json_save(smart_route_with_priority)

    def routes_json_save(self, route:list = None):
        with open('./data/services/wallets_progress.json', 'w') as file:
            accounts_data = {}
            for private_key in WALLETS:
                classic_route = route if route else self.classic_generate_route()
                account_data = {
                    "current_step": 0,
                    "route": classic_route
                }
                accounts_data[private_key] = account_data
            json.dump(accounts_data, file, indent=4)
        self.logger_msg(
            None, None,
            f'Successfully generated {len(accounts_data)} routes in data/services/wallets_progress.json\n', 'success')
