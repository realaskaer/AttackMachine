import asyncio
import os
import json
import time

from functions import *
from web3 import AsyncWeb3
from config import ACCOUNT_NAMES
from modules import Logger
from gspread.utils import rowcol_to_a1
from gspread import Client, Spreadsheet, Worksheet, service_account
from settings import (GOOGLE_SHEET_URL, GOOGLE_SHEET_PAGE_NAME, MODULES_COUNT, ALL_MODULES_TO_RUN,
                      TRANSFER_IN_ROUTES, TRANSFER_COUNT, EXCLUDED_MODULES,
                      DMAIL_IN_ROUTES, DMAIL_COUNT, COLLATERAL_IN_ROUTES, COLLATERAL_COUNT,
                      CLASSIC_ROUTES_MODULES_USING, WITHDRAW_LP, WITHDRAW_LANDING, DEPOSIT_CONFIG)

GSHEET_CONFIG = "./data/services/service_account.json"
os.environ["GSPREAD_SILENCE_WARNINGS"] = "1"

AVAILABLE_MODULES_INFO = {
    # module_name                       : (module name, priority, tg info, can be used in help module, network)
    okx_withdraw                        : (okx_withdraw, -1, 'OKX Withdraw', 0, [3, 4, 8, 9, 11]),
    deploy_stark_wallet                 : (deploy_stark_wallet, 0, 'Deploy Wallet', 0, [9]),
    bridge_rhino                        : (bridge_rhino, 1, 'Rhino Bridge', 0, [3, 4, 8, 9, 11]),
    bridge_layerswap                    : (bridge_layerswap, 1, 'LayerSwap Bridge', 0, [3, 4, 8, 9, 11]),
    bridge_orbiter                      : (bridge_orbiter, 1, 'Orbiter Bridge', 0, [3, 4, 8, 9, 11]),
    bridge_native                       : (bridge_native, 1, 'Native Bridge', 0, [3, 4, 8, 9, 11]),
    upgrade_stark_wallet                : (upgrade_stark_wallet, 2, 'Upgrade Wallet', 0, [9]),
    add_liquidity_maverick              : (add_liquidity_maverick, 2, 'Maverick Liquidity', 0, [11]),
    add_liquidity_mute                  : (add_liquidity_mute, 2, 'Mute Liquidity', 0, [11]),
    add_liquidity_syncswap              : (add_liquidity_syncswap, 2, 'SyncSwap Liquidity', 0, [11]),
    deposit_basilisk                    : (deposit_basilisk, 2, 'Basilisk Deposit', 0, [11]),
    deposit_eralend                     : (deposit_eralend, 2, 'EraLend Deposit', 0, [11]),
    deposit_reactorfusion               : (deposit_reactorfusion, 2, 'ReactorFusion Deposit', 0, [11]),
    deposit_zerolend                    : (deposit_zerolend, 2, 'ZeroLend Deposit', 0, [11]),
    deposit_nostra                      : (deposit_nostra, 2, 'Nostra Deposit', 0, [9]),
    deposit_zklend                      : (deposit_zklend, 2, 'zkLend Deposit', 0, [9]),
    deposit_layerbank                   : (deposit_layerbank, 2, 'LayerBank Deposit', 0, [4, 8]),
    deposit_rocketsam                   : (deposit_rocketsam, 2, 'RocketSam Deposit', 0, [3, 4, 8, 11]),
    enable_collateral_basilisk          : (enable_collateral_basilisk, 2, 'Basilisk Collateral', 1, [11]),
    enable_collateral_eralend           : (enable_collateral_eralend, 2, 'EraLend Collateral', 1, [11]),
    enable_collateral_reactorfusion     : (enable_collateral_reactorfusion, 2, 'ReactorFusion Collateral', 1, [11]),
    enable_collateral_zklend            : (enable_collateral_zklend, 2, 'zkLend Collateral', 1, [9]),
    enable_collateral_layerbank         : (enable_collateral_layerbank, 2, 'LayerBank Collateral', 1, [4, 8]),
    swap_jediswap                       : (swap_jediswap, 2, 'JediSwap Swap', 1, [9]),
    swap_avnu                           : (swap_avnu, 2, 'AVNU Swap', 1, [9]),
    swap_10kswap                        : (swap_10kswap, 2, '10kSwap Swap', 1, [9]),
    swap_sithswap                       : (swap_sithswap, 2, 'SithSwap Swap', 1, [9]),
    swap_protoss                        : (swap_protoss, 2, 'Protoss Swap', 1, [9]),
    swap_myswap                         : (swap_myswap, 2, 'mySwap Swap', 1, [9]),
    swap_izumi                          : (swap_izumi, 2, 'iZumi Swap', 1, [3, 4, 8, 11]),
    swap_maverick                       : (swap_maverick, 2, 'Maverick Swap', 1, [3, 11]),
    swap_mute                           : (swap_mute, 2, 'Mute Swap', 1, [11]),
    swap_odos                           : (swap_odos, 2, 'ODOS Swap', 1, [3, 11]),
    swap_oneinch                        : (swap_oneinch, 2, '1inch Swap', 1, [3, 11]),
    swap_openocean                      : (swap_openocean, 2, 'OpenOcean Swap', 0, [3, 4, 8, 11]),
    swap_pancake                        : (swap_pancake, 2, 'Pancake Swap', 1, [3, 4, 11]),
    swap_spacefi                        : (swap_spacefi, 2, 'SpaceFi Swap', 1, [8, 11]),
    swap_rango                          : (swap_rango, 2, 'Rango Swap', 1, [4, 11]),
    swap_xyfinance                      : (swap_xyfinance, 2, 'XYfinance Swap', 0, [11]),
    swap_syncswap                       : (swap_syncswap, 2, 'SyncSwap Swap', 1, [4, 8, 11]),
    swap_velocore                       : (swap_velocore, 2, 'Velocore Swap', 1, [4, 11]),
    swap_vesync                         : (swap_vesync, 2, 'VeSync Swap', 1, [11]),
    swap_woofi                          : (swap_woofi, 2, 'WooFi Swap', 1, [3, 4, 11]),
    swap_zkswap                         : (swap_zkswap, 2, 'zkSwap Swap', 1, [11]),
    swap_uniswap                        : (swap_uniswap, 2, 'Uniswap Swap', 1, [3, 11]),
    swap_sushiswap                      : (swap_sushiswap, 2, 'SushiSwap Swap', 1, [3, 11]),
    wrap_eth                            : (wrap_eth, 2, 'Wrap ETH', 0, [11]),
    random_approve                      : (random_approve, 2, 'Random Approve', 0, [3, 4, 8, 9, 11]),
    disable_collateral_basilisk         : (disable_collateral_basilisk, 3, 'Basilisk Collateral', 1, [11]),
    disable_collateral_eralend          : (disable_collateral_eralend, 3, 'EraLend Collateral', 1, [11]),
    disable_collateral_reactorfusion    : (disable_collateral_reactorfusion, 3, 'ReactorFusion Collateral', 1, [11]),
    disable_collateral_layerbank        : (disable_collateral_layerbank, 3, 'LayerBank Collateral', 1, [4, 8]),
    create_omnisea                      : (create_omnisea, 2, 'Omnisea Create NFT', 0, [4, 8, 11]),
    create_safe                         : (create_safe, 2, 'Gnosis Safe', 0, [3, 11]),
    mint_and_bridge_l2telegraph         : (mint_and_bridge_l2telegraph, 3, 'L2Telegraph NFT bridge', 0, [3, 4, 8, 11]),
    mint_domain_ens                     : (mint_domain_ens, 2, 'ENS Domain Mint', 0, [11]),
    mint_domain_zns                     : (mint_domain_zns, 2, 'ZNS Domain Mint', 0, [11]),
    mint_mailzero                       : (mint_mailzero, 2, 'MailZero NFT mint', 0, [11]),
    mint_tevaera                        : (mint_tevaera, 2, 'Tevaera ID & NFT mint', 0, [11]),
    mint_zerius                         : (mint_zerius, 2, 'Zerius Mint NFT', 0, [3, 4, 8, 11]),
    mint_starknet_identity              : (mint_starknet_identity, 2, 'Mint Starknet ID', 0, [9]),
    mint_starkstars                     : (mint_starkstars, 2, 'StarkStars Mint', 0, [9]),
    mint_zkstars                        : (mint_zkstars, 2, 'zkStars Mint', 0, [3, 4, 8, 11]),
    deploy_contract                     : (deploy_contract, 3, 'Contract Deploy', 0, [3, 4, 8, 9, 11]),
    bridge_zerius                       : (bridge_zerius, 3, 'Zerius Bridge NFT', 0, [3, 4, 8, 11]),
    refuel_bungee                       : (refuel_bungee, 3, 'Bungee Refuel', 0, [3, 11]),
    refuel_merkly                       : (refuel_merkly, 3, 'Merkly Refuel', 0, [3, 4, 8, 11]),
    refuel_zerius                       : (refuel_zerius, 3, 'Zerius Refuel', 0, [3, 4, 8, 11]),
    send_message_dmail                  : (send_message_dmail, 2, 'Dmail Message', 1, [3, 4, 8, 9, 11]),
    send_message_l2telegraph            : (send_message_l2telegraph, 2, 'L2Telegraph Message', 0, [3, 4, 8, 11]),
    transfer_eth                        : (transfer_eth, 2, 'Transfer ETH', 0, [9, 11]),
    transfer_eth_to_myself              : (transfer_eth_to_myself, 2, 'Transfer ETH to myself', 0, [9, 11]),
    withdraw_liquidity_maverick         : (withdraw_liquidity_maverick, 3, 'Maverick Withdraw', 0, [11]),
    withdraw_liquidity_mute             : (withdraw_liquidity_mute, 3, 'Mute Withdraw', 0, [11]),
    withdraw_liquidity_syncswap         : (withdraw_liquidity_syncswap, 3, 'SyncSwap Withdraw', 0, [11]),
    withdraw_basilisk                   : (withdraw_basilisk, 3, 'Basilisk Withdraw', 0, [11]),
    withdraw_eralend                    : (withdraw_eralend, 3, 'EraLend Withdraw', 0, [11]),
    withdraw_reactorfusion              : (withdraw_reactorfusion, 3, 'ReactorFusion Withdraw', 0, [11]),
    withdraw_zerolend                   : (withdraw_zerolend, 3, 'ZeroLend Withdraw', 0, [11]),
    withdraw_nostra                     : (withdraw_nostra, 3, 'Nostra Withdraw', 0, [9]),
    withdraw_zklend                     : (withdraw_zklend, 3, 'zkLend Withdraw', 0, [9]),
    withdraw_layerbank                  : (withdraw_layerbank, 3, 'LayerBank Withdraw', 0, [4, 8]),
    withdraw_rocketsam                  : (withdraw_rocketsam, 3, 'RocketSam Withdraw', 0, [3, 4, 8, 11]),
    withdraw_native_bridge              : (withdraw_native_bridge, 3, 'Native Bridge Withdraw', 0, [9, 11]),
    okx_deposit                         : (okx_deposit, 4, 'OKX Deposit', 0, [3, 4, 8, 9, 11]),
    okx_collect_from_sub                : (okx_collect_from_sub, 5, 'OKX Collect money', 0, [3, 4, 8, 9, 11])
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
        self.w3 = AsyncWeb3()
        if GLOBAL_NETWORK == 11:
            map_data = {
                'Syncswap Liquidity': add_liquidity_syncswap,
                'Maverick Liquidity': add_liquidity_maverick,
                'Mute Liquidity': add_liquidity_mute,
                'Syncswap Swap': swap_syncswap,
                'Mute Swap': swap_mute,
                'Maverick Swap': swap_maverick,
                'iZumi Swap': swap_izumi,
                'Rango Swap': swap_rango,
                'VeSync Swap': swap_vesync,
                'SpaceFi Swap': swap_spacefi,
                'Pancake Swap': swap_pancake,
                'WooFi Swap': swap_woofi,
                'ODOS Swap': swap_odos,
                'zkSwap Swap': swap_zkswap,
                'XYfinance Swap': swap_xyfinance,
                'Velocore Swap': swap_velocore,
                '1inch Swap': swap_oneinch,
                'Openocean Swap': swap_openocean,
                'EraLend Deposit': deposit_eralend,
                'ZeroLend Deposit': deposit_zerolend,
                'Basilisk Deposit': deposit_basilisk,
                'RocketSam Deposit': deposit_rocketsam,
                'Reactorfusion Deposit': deposit_reactorfusion,
                'Zerius Mint NFT': mint_zerius,
                'Zerius Bridge NFT': bridge_zerius,
                'Omnisea Create NFT': create_omnisea,
                'Tavaera ID & NFT Mint': mint_tevaera,
                'Mailzero NFT Mint': mint_mailzero,
                'ZNS Domain Mint': mint_domain_zns,
                'ENS Domain Mint': mint_domain_ens,
                'L2Telegraph NFT Bridge': mint_and_bridge_l2telegraph,
                'Gnosis Safe': create_safe,
                'Contract Deploy': deploy_contract,
                'L2Telegraph Message': send_message_l2telegraph,
                'Zerius Refuel': refuel_zerius,
                'Merkly Refuel': refuel_merkly,
                'Bungee Refuel': refuel_bungee,
                'Withdraw txSync': withdraw_native_bridge,
            }
        elif GLOBAL_NETWORK == 9:
            map_data = {
                'mySwap Swap': swap_myswap,
                'Jediswap Swap': swap_jediswap,
                '10kSwap Swap': swap_10kswap,
                'SithSwap Swap': swap_sithswap,
                'Protoss Swap': swap_protoss,
                'Avnu Swap': swap_avnu,
                'zkLend Deposit': deposit_zklend,
                'Nostra Deposit': deposit_nostra,
                'Mint Starknet ID': mint_starknet_identity,
                'Mint StarkStars': mint_starkstars,
            }
        elif GLOBAL_NETWORK == 3:
            map_data = {
                'PancakeSwap Swap': swap_pancake,
                'Uniswap Swap':  swap_uniswap,
                'SushiSwap Swap':  swap_sushiswap,
                'WooFi Swap': swap_woofi,
                'Maverick Swap': swap_maverick,
                'iZumi Swap': swap_izumi,
                'ODOS Swap': swap_odos,
                '1inch Swap': swap_oneinch,
                'OpenOcean Swap': swap_openocean,
                'XYfinance Swap': swap_xyfinance,
                'RocketSam Deposit': deposit_rocketsam,
                'Gnosis Safe Create': create_safe,
                'zkStars Mint': mint_zkstars,
                'Zerius Mint': mint_zerius,
                'Zerius Bridge': bridge_zerius,
                'L2Telegraph Bridge NFT': mint_and_bridge_l2telegraph,
                'Contract Deploy': deploy_contract,
                'Bungee Refuel': refuel_bungee,
                'Merkly Refuel': refuel_merkly,
                'Zerius Refuel': refuel_zerius,
                'L2Telegraph Message': send_message_l2telegraph,
            }
        elif GLOBAL_NETWORK == 4:
            map_data = {
                'SyncSwap Swap': swap_syncswap,
                'PancakeSwap Swap': swap_pancake,
                'WooFi Swap': swap_woofi,
                'Velocore Swap': swap_velocore,
                'iZumi Swap': swap_izumi,
                'Rango Swap': swap_rango,
                'OpenOcean Swap': swap_openocean,
                'XYfinance Swap': swap_xyfinance,
                'LayerBank Deposit': deposit_layerbank,
                'RocketSam Deposit': deposit_rocketsam,
                'OmniSea Create': create_omnisea,
                'zkStars Mint': mint_zkstars,
                'Zerius Mint': mint_zerius,
                'Zerius Bridge': bridge_zerius,
                'L2Telegraph Bridge NFT': mint_and_bridge_l2telegraph,
                'Contract Deploy': deploy_contract,
                'Merkly Refuel': refuel_merkly,
                'Zerius Refuel': refuel_zerius,
                'L2Telegraph Message': send_message_l2telegraph,
            }
        elif GLOBAL_NETWORK == 8:
            map_data = {
                'SyncSwap Swap': swap_syncswap,
                'SpaceFi Swap': swap_spacefi,
                'iZumi Swap': swap_izumi,
                'OpenOcean Swap': swap_openocean,
                'XYfinance Swap': swap_xyfinance,
                'LayerBank Deposit': deposit_layerbank,
                'RocketSam Deposit': deposit_rocketsam,
                'OmniSea Create': create_omnisea,
                'zkStars Mint':  mint_zkstars,
                'Zerius Mint': mint_zerius,
                'Zerius Bridge': bridge_zerius,
                'L2Telegraph Bridge NFT': mint_and_bridge_l2telegraph,
                'Contract Deploy': deploy_contract,
                'Merkly Refuel': refuel_merkly,
                'Zerius Refuel': refuel_zerius,
                'L2Telegraph Message': send_message_l2telegraph,
            }
        else:
            self.logger_msg(None, None,
                            msg=f"This network does not support in Google SpreadSheets", type_msg='error')
            raise RuntimeError('Bad GLOBAL_NETWORK')
        self.function_mappings = map_data

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

    def get_account_name_list(self):
        try:
            return self.ws.col_values(1)[1:]
        except Exception as error:
            self.logger_msg(None, None, f"Put data into 'GOOGLE_SHEET_URL' and 'service_accounts.json' first!", 'error')
            raise RuntimeError(f"{error}")

    async def update_sheet(self, result_list: list, result_count: tuple):
        batch_size = 200
        for i in range(0, len(result_list), batch_size):
            batch_results = result_list[i:i + batch_size]
            total_results_to_update = []
            for item in batch_results:
                sheet_cell = rowcol_to_a1(row=item['row'], col=item['col'])
                total_results_to_update.append({
                    'range': sheet_cell,
                    'values': [[item['result']]],
                })
            self.ws.batch_update(total_results_to_update, value_input_option="USER_ENTERED")

        info = f'Google Sheet updated! Modules results info: ✅ - {result_count[0]} | ❌ - {result_count[1]}'
        self.logger_msg(None, None, info, 'success')
        return True

    def get_modules_list(self):
        modules_list_str = self.ws.row_values(1)[2:]

        modules_list = []
        for module in modules_list_str:
            if module in self.function_mappings:
                modules_list.append(self.function_mappings[module])
        return modules_list

    def get_data_for_batch(self, account_names:list):
        wallet_list = self.get_account_name_list()
        batch_size = 200
        data_to_return = {}

        for i in range(0, len(account_names), batch_size):
            batch_account_names = account_names[i:i+batch_size]
            batch_data = self.get_data_for_single_batch(batch_account_names, wallet_list)
            data_to_return.update(batch_data)

        return data_to_return

    def get_data_for_single_batch(self, batch_account_names:list, wallet_list:list):
        ranges_for_sheet = []
        batch_data = {}
        data_to_return = {}
        col = 2 + len(self.function_mappings)

        for account_name in batch_account_names:
            row = 2 + wallet_list.index(account_name)
            batch_data[row] = {
                'account_name': account_name
            }
            sheet_range = f"{rowcol_to_a1(row=row, col=3)}:{rowcol_to_a1(row=row, col=col)}"
            ranges_for_sheet.append(sheet_range)

        full_data = self.ws.batch_get(ranges_for_sheet)

        for index, data in enumerate(batch_data.items()):
            k, v = data
            data_to_return[v['account_name']] = {
                'progress': full_data[index]
            }

        return data_to_return

    async def get_smart_routes_for_batch(self, accounts_names:list):
        batch_data = self.get_data_for_batch(accounts_names)
        modules_list = self.get_modules_list()
        tasks = []
        for accounts_names in accounts_names:
            tasks.append(self.get_smart_route(accounts_names, batch_data[accounts_names]['progress'][0],
                         batch_mode=True, modules_list=modules_list))
        await asyncio.gather(*tasks)

    async def get_smart_route(self, account_name: str, wallet_statuses:list = None,
                              batch_mode:bool = False, modules_list:list = None):
        if not batch_mode:
            wallets_list = self.get_account_name_list()
            modules_list = self.get_modules_list()

            wallet_modules_statuses = self.ws.row_values(wallets_list.index(account_name) + 2)[2:]
        else:
            wallet_modules_statuses = wallet_statuses

        modules_to_work = []
        collaterals_modules = []
        transfers_modules = [transfer_eth_to_myself, transfer_eth]

        if GLOBAL_NETWORK == 11:
            collaterals_modules = [enable_collateral_eralend, enable_collateral_basilisk,
                                   enable_collateral_reactorfusion, disable_collateral_basilisk,
                                   disable_collateral_eralend, disable_collateral_reactorfusion,]
        elif GLOBAL_NETWORK == 9:
            collaterals_modules = [enable_collateral_zklend, disable_collateral_zklend]
            transfers_modules = []
        elif GLOBAL_NETWORK in [4, 8]:
            collaterals_modules = [enable_collateral_layerbank, disable_collateral_layerbank]

        for i in range(len(wallet_modules_statuses)):
            if wallet_modules_statuses[i] in ["Not Started", "Error"]:
                modules_to_work.append(modules_list[i])

        excluded_modules = [get_func_by_name(module) for module in EXCLUDED_MODULES
                            if get_func_by_name(module) in list(self.function_mappings.values())]

        possible_modules = [module for module in modules_to_work if module not in excluded_modules]

        want_count = len(modules_to_work) if ALL_MODULES_TO_RUN else random.choice(MODULES_COUNT)
        possible_count = min(want_count, len(possible_modules))

        possible_modules_data = [AVAILABLE_MODULES_INFO[module] for module in possible_modules]

        smart_route: list = random.sample(possible_modules_data, possible_count)

        if DMAIL_IN_ROUTES:
            smart_route.extend([AVAILABLE_MODULES_INFO[send_message_dmail] for _ in range(random.choice(DMAIL_COUNT))])

        if COLLATERAL_IN_ROUTES and collaterals_modules:
            smart_route.extend([AVAILABLE_MODULES_INFO[random.choice(collaterals_modules)]
                                for _ in range(random.choice(COLLATERAL_COUNT))])

        if TRANSFER_IN_ROUTES and transfers_modules:
            smart_route.extend([AVAILABLE_MODULES_INFO[random.choice(transfers_modules)]
                                for _ in range(random.choice(TRANSFER_COUNT))])

        if WITHDRAW_LP:
            if GLOBAL_NETWORK == 11:
                smart_route.append(AVAILABLE_MODULES_INFO[withdraw_liquidity_maverick])
                smart_route.append(AVAILABLE_MODULES_INFO[withdraw_liquidity_mute])
                smart_route.append(AVAILABLE_MODULES_INFO[withdraw_liquidity_syncswap])

        if WITHDRAW_LANDING:
            if GLOBAL_NETWORK == 11:
                smart_route.append(AVAILABLE_MODULES_INFO[withdraw_eralend])
                smart_route.append(AVAILABLE_MODULES_INFO[withdraw_reactorfusion])
                smart_route.append(AVAILABLE_MODULES_INFO[withdraw_basilisk])
                smart_route.append(AVAILABLE_MODULES_INFO[withdraw_zerolend])
            elif GLOBAL_NETWORK == 9:
                smart_route.append(AVAILABLE_MODULES_INFO[withdraw_zklend])
                smart_route.append(AVAILABLE_MODULES_INFO[withdraw_nostra])
            elif GLOBAL_NETWORK in [4, 8]:
                smart_route.append(AVAILABLE_MODULES_INFO[withdraw_layerbank])
                smart_route.append(AVAILABLE_MODULES_INFO[withdraw_rocketsam])

        bridge_modules = [AVAILABLE_MODULES_INFO[bridge_rhino] if DEPOSIT_CONFIG['bridge_rhino'] else None,
                          AVAILABLE_MODULES_INFO[bridge_layerswap] if DEPOSIT_CONFIG['bridge_layerswap'] else None,
                          AVAILABLE_MODULES_INFO[bridge_orbiter] if DEPOSIT_CONFIG['bridge_orbiter'] else None,
                          AVAILABLE_MODULES_INFO[bridge_native] if DEPOSIT_CONFIG['bridge_native'] else None]

        bridge_to_add = [i for i in bridge_modules if i]

        if bridge_to_add:
            smart_route.append(random.choice(bridge_to_add))

        smart_route.append(AVAILABLE_MODULES_INFO[okx_withdraw] if DEPOSIT_CONFIG['okx_withdraw'] else None)
        smart_route.append(AVAILABLE_MODULES_INFO[okx_deposit] if DEPOSIT_CONFIG['okx_deposit'] else None)
        smart_route.append(
            AVAILABLE_MODULES_INFO[okx_collect_from_sub] if DEPOSIT_CONFIG['okx_collect_from_sub'] else None)
        smart_route.append(
            AVAILABLE_MODULES_INFO[upgrade_stark_wallet] if DEPOSIT_CONFIG['upgrade_stark_wallet'] else None)
        smart_route.append(
            AVAILABLE_MODULES_INFO[deploy_stark_wallet] if DEPOSIT_CONFIG['deploy_stark_wallet'] else None)

        random.shuffle(smart_route)

        smart_route_with_priority = [i[0].__name__ for i in sorted(list(filter(None, smart_route)), key=lambda x: x[1])]

        self.smart_routes_json_save(account_name, smart_route_with_priority)

    def classic_routes_json_save(self):
        with open('./data/services/wallets_progress.json', 'w') as file:
            accounts_data = {}
            for account_name in ACCOUNT_NAMES:
                classic_route = self.classic_generate_route()
                account_data = {
                    "current_step": 0,
                    "route": classic_route
                }
                accounts_data[str(account_name)] = account_data
            json.dump(accounts_data, file, indent=4)
        self.logger_msg(
            None, None,
            f'Successfully generated {len(accounts_data)} classic routes in data/services/wallets_progress.json\n',
            'success')

    def smart_routes_json_save(self, account_name:str, route:list):
        progress_file_path = './data/services/wallets_progress.json'
        try:
            with open(progress_file_path, 'r+') as file:
                data = json.load(file)
        except json.JSONDecodeError:
            data = {}

        data[account_name] = {
            "current_step": 0,
            "route": route
        }

        with open(progress_file_path, 'w') as file:
            json.dump(data, file, indent=4)

        self.logger_msg(
            None, None,
            f'Successfully generated smart routes for {account_name}', 'success')

    def save_google_progress_offline(self, accounts_progress):
        bad_progress_file_path = './data/services/google_progress.json'
        try:
            with open(bad_progress_file_path, 'r') as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}

        data[f"{time.time()}"] = f'{accounts_progress}'

        with open(bad_progress_file_path, 'w') as file:
            json.dump(data, file, indent=4)

        self.logger_msg(
            None, None, 'Successfully saved progress in files', 'success')
