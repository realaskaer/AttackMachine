import asyncio
import copy
import os
import json
import random

from utils.tools import clean_progress_file
from functions import *
from web3 import AsyncWeb3
from config import ACCOUNT_NAMES
from modules import Logger
from modules.interfaces import SoftwareException
from gspread.utils import rowcol_to_a1
from gspread import Client, Spreadsheet, Worksheet, service_account
from general_settings import GOOGLE_SHEET_URL, GOOGLE_SHEET_PAGE_NAME, GLOBAL_NETWORK, SHUFFLE_ROUTE
from settings import (MODULES_COUNT, ALL_MODULES_TO_RUN, TRANSFER_COUNT, EXCLUDED_MODULES, DMAIL_COUNT,
                      COLLATERAL_COUNT, CLASSIC_ROUTES_MODULES_USING, WITHDRAW_LP, WITHDRAW_LANDING, HELPERS_CONFIG,
                      CLASSIC_WITHDRAW_DEPENDENCIES, INCLUDED_MODULES, WRAPS_COUNT)

GSHEET_CONFIG = "./data/services/service_account.json"
os.environ["GSPREAD_SILENCE_WARNINGS"] = "1"


AVAILABLE_MODULES_INFO = {
    # module_name                       : (module name, priority, tg info, can be help module, supported network)
    okx_withdraw                        : (okx_withdraw, -3, 'OKX withdraw', 0, []),
    bingx_withdraw                      : (bingx_withdraw, -3, 'BingX withdraw', 0, []),
    binance_withdraw                    : (binance_withdraw, -3, 'Binance withdraw', 0, []),
    bitget_withdraw                     : (bitget_withdraw, -3, 'Bitget withdraw', 0, []),
    make_balance_to_average             : (make_balance_to_average, -2, 'Check and make wanted balance', 0, []),
    bridge_rhino                        : (bridge_rhino, 1, 'Rhino bridge', 0, [2, 3, 4, 8, 9, 11, 12]),
    bridge_layerswap                    : (bridge_layerswap, 1, 'LayerSwap bridge', 0, [2, 3, 4, 8, 9, 11, 12]),
    bridge_orbiter                      : (bridge_orbiter, 1, 'Orbiter bridge', 0, [2, 3, 4, 8, 9, 11, 12]),
    bridge_across                       : (bridge_across, 1, 'Across bridge', 0, [2, 3, 11, 12]),
    bridge_bungee                       : (bridge_bungee, 1, 'Bungee bridge', 0, [2, 3, 11, 12]),
    bridge_owlto                        : (bridge_owlto, 1, 'Owlto bridge', 0, [2, 3, 11, 12]),
    bridge_relay                        : (bridge_relay, 1, 'Relay bridge', 0, [2, 3, 11, 12]),
    bridge_nitro                        : (bridge_nitro, 1, 'Nitro bridge', 0, [2, 3, 11, 12]),
    bridge_native                       : (bridge_native, 1, 'Native bridge', 0, [2, 3, 4, 8, 9, 11, 12]),
    bridge_zora                         : (bridge_zora, 1, 'Zora instant bridge', 0, [2, 3, 4, 8, 9, 11, 12]),
    add_liquidity_maverick              : (add_liquidity_maverick, 2, 'Maverick add liquidity', 0, [11]),
    add_liquidity_mute                  : (add_liquidity_mute, 2, 'Mute add liquidity', 0, [11]),
    add_liquidity_syncswap              : (add_liquidity_syncswap, 2, 'SyncSwap add liquidity', 0, [11]),
    deposit_basilisk                    : (deposit_basilisk, 2, 'Basilisk deposit', 0, [11]),
    deposit_eralend                     : (deposit_eralend, 2, 'EraLend deposit', 0, [11]),
    deposit_reactorfusion               : (deposit_reactorfusion, 2, 'ReactorFusion deposit', 0, [11]),
    deposit_zerolend                    : (deposit_zerolend, 2, 'ZeroLend deposit', 0, [11]),
    deposit_usdb_zerolend               : (deposit_usdb_zerolend, 2, 'ZeroLend USDB deposit', 0, [11]),
    deposit_layerbank                   : (deposit_layerbank, 2, 'LayerBank deposit', 0, [0]),
    deposit_rocketsam                   : (deposit_rocketsam, 2, 'RocketSam deposit', 0, [0]),
    deposit_moonwell                    : (deposit_moonwell, 2, 'Moonwell deposit', 0, [0]),
    deposit_seamless                    : (deposit_seamless, 2, 'Seamless deposit', 0, [0]),
    deposit_usdbc_seamless              : (deposit_usdbc_seamless, 2, 'Seamless USDbC deposit', 0, [0]),
    enable_collateral_basilisk          : (enable_collateral_basilisk, 2, 'Enable Basilisk collateral', 1, [11]),
    enable_collateral_eralend           : (enable_collateral_eralend, 2, 'Enable EraLend collateral', 1, [11]),
    enable_collateral_reactorfusion     : (enable_collateral_reactorfusion, 2, 'Enable ReactorFusion collateral', 1, [11]),
    enable_collateral_layerbank         : (enable_collateral_layerbank, 2, 'Enable LayerBank collateral', 1, [4, 8]),
    enable_collateral_seamless          : (enable_collateral_seamless, 2, 'Enable Seamless collateral', 1, [4, 8]),
    enable_collateral_moonwell          : (enable_collateral_moonwell, 2, 'Enable Moonwell collateral', 1, [4, 8]),
    smart_stake_stg                     : (smart_stake_stg, 2, 'Stake STG on Stargate', 0, [0]),
    bridge_stargate_dust                : (bridge_stargate_dust, 2, 'Stargate Bridge Dust', 0, [0]),
    bridge_stargate                     : (bridge_stargate, 2, 'Stargate bridge', 0, [0]),
    bridge_coredao                      : (bridge_coredao, 2, 'CoreDAO bridge', 0, [0]),
    custom_swap                         : (custom_swap, 2, 'Custom swap', 0, [3, 4, 8, 11]),
    swap_ambient                        : (swap_ambient, 2, 'Ambient swap', 1, [3, 4, 8, 11]),
    swap_bebop                          : (swap_bebop, 2, 'Bebop swap', 1, [3, 4, 8, 11]),
    swap_thruster                       : (swap_thruster, 2, 'Thruster swap', 1, [3, 4, 8, 11]),
    swap_bladeswap                      : (swap_bladeswap, 2, 'BladeSwap swap', 1, [3, 4, 8, 11]),
    swap_zebra                          : (swap_zebra, 2, 'Zebra swap', 1, [3, 4, 8, 11]),
    swap_skydrome                       : (swap_skydrome, 2, 'Skydrome swap', 1, [3, 4, 8, 11]),
    swap_izumi                          : (swap_izumi, 2, 'iZumi swap', 1, [3, 4, 8, 11]),
    swap_maverick                       : (swap_maverick, 2, 'Maverick swap', 1, [3, 11]),
    swap_mute                           : (swap_mute, 2, 'Mute swap', 1, [11]),
    swap_odos                           : (swap_odos, 2, 'ODOS swap', 1, [3, 11]),
    swap_oneinch                        : (swap_oneinch, 2, '1inch swap', 1, [3, 11]),
    swap_openocean                      : (swap_openocean, 2, 'OpenOcean swap', 0, [3, 4, 8, 11]),
    swap_pancake                        : (swap_pancake, 2, 'Pancake swap', 1, [3, 4, 11]),
    swap_spacefi                        : (swap_spacefi, 2, 'SpaceFi swap', 1, [8, 11]),
    swap_rango                          : (swap_rango, 2, 'Rango swap', 1, [4, 11]),
    swap_xyfinance                      : (swap_xyfinance, 2, 'XYfinance swap', 0, []),
    swap_syncswap_paymaster             : (swap_syncswap_paymaster, 2, 'SyncSwap paymaster swap', 1, [4, 8, 11]),
    swap_syncswap                       : (swap_syncswap, 2, 'SyncSwap swap', 1, [4, 8, 11]),
    swap_velocore                       : (swap_velocore, 2, 'Velocore swap', 1, [4, 11]),
    swap_vesync                         : (swap_vesync, 2, 'VeSync swap', 1, [11]),
    swap_woofi                          : (swap_woofi, 2, 'WooFi swap', 1, [3, 4, 11]),
    swap_zkswap                         : (swap_zkswap, 2, 'zkSwap swap', 1, [11]),
    swap_uniswap                        : (swap_uniswap, 2, 'Uniswap swap', 1, [3]),
    swap_sushiswap                      : (swap_sushiswap, 2, 'SushiSwap swap', 1, [2, 3]),
    swap_bridged_usdc                   : (swap_bridged_usdc, 2, 'Swap USDC to Bridged', 0, [0]),
    wrap_eth                            : (wrap_eth, 2, 'Wrap ETH', 0, []),
    unwrap_eth                          : (unwrap_eth, 2, 'Unwrap ETH', 0, []),
    random_approve                      : (random_approve, 2, 'Random approve', 0, []),
    smart_random_approve                : (smart_random_approve, 2, 'Smart random approve', 0, []),
    disable_collateral_basilisk         : (disable_collateral_basilisk, 3, 'Disable Basilisk collateral', 1, [11]),
    disable_collateral_eralend          : (disable_collateral_eralend, 3, 'Disable EraLend collateral', 1, [11]),
    disable_collateral_reactorfusion    : (disable_collateral_reactorfusion, 3, 'Disable ReactorFusion collateral', 1, [11]),
    disable_collateral_layerbank        : (disable_collateral_layerbank, 3, 'Disable LayerBank collateral', 1, [4, 8]),
    disable_collateral_seamless         : (disable_collateral_seamless, 3, 'Disable Seamless collateral', 1, [4, 8]),
    disable_collateral_moonwell         : (disable_collateral_moonwell, 3, 'Disable Moonwell collateral', 1, [4, 8]),
    create_omnisea                      : (create_omnisea, 2, 'Omnisea create NFT', 0, [4, 8, 11]),
    create_safe                         : (create_safe, 2, 'Gnosis Safe', 0, [3, 11]),
    mint_and_bridge_l2telegraph         : (mint_and_bridge_l2telegraph, 3, 'L2Telegraph NFT bridge', 0, []),
    bridge_hyperlane_nft                : (bridge_hyperlane_nft, 3, 'Merkly Hyperlane NFT bridge', 0, []),
    bridge_hyperlane_token              : (bridge_hyperlane_token, 3, 'Merkly Hyperlane Tokens bridge', 0, []),
    mint_domain_ens                     : (mint_domain_ens, 2, 'ENS domain mint', 0, [11]),
    mint_domain_zns                     : (mint_domain_zns, 2, 'ZNS domain mint', 0, [11]),
    mint_mailzero                       : (mint_mailzero, 2, 'MailZero NFT mint', 0, [11]),
    mint_tevaera                        : (mint_tevaera, 2, 'Tevaera ID & NFT mint', 0, [11]),
    mint_zkstars                        : (mint_zkstars, 2, 'zkStars mint', 0, [3, 4, 8, 11, 12]),
    mint_mintfun                        : (mint_mintfun, 2, 'Mintfun mint', 0, [3, 4, 8, 11]),
    mint_hypercomic                     : (mint_hypercomic, 2, 'HyperComic mint', 0, [11]),
    claim_rewards_bungee                : (claim_rewards_bungee, 2, 'Claim Socket rewards', 0, [11]),
    claim_op_across                     : (claim_op_across, 2, 'Claim OP on Across', 0, [11]),
    rhino_recovery_funds                : (rhino_recovery_funds, 2, 'Rhino refund', 0, [11]),
    grapedraw_bid                       : (grapedraw_bid, 2, 'Bid place on GrapeDraw', 1, [3, 11]),
    vote_rubyscore                      : (vote_rubyscore, 2, 'Vote on RubyScore', 1, [3, 4, 8, 11]),
    deploy_contract                     : (deploy_contract, 3, 'Contract deploy', 0, []),
    bridge_zerius                       : (bridge_zerius, 3, 'Zerius bridge NFT', 0, []),
    bridge_merkly                       : (bridge_merkly, 3, 'Merkly bridge NFT', 0, []),
    bridge_l2pass                       : (bridge_l2pass, 3, 'L2Pass bridge NFT', 0, []),
    bridge_nogem                        : (bridge_nogem, 3, 'nogem.app bridge NFT', 0, []),
    bridge_whale                        : (bridge_whale, 3, 'Whale bridge NFT', 0, []),
    refuel_bungee                       : (refuel_bungee, 3, 'Bungee refuel', 0, []),
    refuel_merkly                       : (refuel_merkly, 3, 'Merkly refuel', 0, []),
    refuel_l2pass                       : (refuel_l2pass, 3, 'L2Pass refuel', 0, []),
    refuel_nogem                        : (refuel_nogem, 3, 'nogem.app refuel', 0, []),
    refuel_zerius                       : (refuel_zerius, 3, 'Zerius refuel', 0, []),
    refuel_whale                        : (refuel_whale, 3, 'Whale refuel', 0, []),
    zerius_refuel_attack                : (zerius_refuel_attack, 3, 'Zerius refuel attack', 0, []),
    merkly_refuel_attack                : (merkly_refuel_attack, 3, 'Merkly refuel attack', 0, []),
    l2pass_refuel_attack                : (l2pass_refuel_attack, 3, 'L2Pass refuel attack', 0, []),
    nogem_refuel_attack                 : (nogem_refuel_attack, 3, 'nogem.app refuel attack', 0, []),
    whale_refuel_attack                 : (whale_refuel_attack, 3, 'Whale refuel attack', 0, []),
    zerius_refuel_google                : (zerius_refuel_google, 3, 'Zerius google refuel', 0, []),
    nogem_refuel_google                 : (nogem_refuel_google, 3, 'nogem.app google refuel', 0, []),
    merkly_refuel_google                : (merkly_refuel_google, 3, 'Merkly google refuel', 0, []),
    l2pass_refuel_google                : (l2pass_refuel_google, 3, 'L2Pass google refuel', 0, []),
    whale_refuel_google                 : (whale_refuel_google, 3, 'Whale google refuel', 0, []),
    zerius_bridge_google                : (zerius_bridge_google, 3, 'Zerius google bridge', 0, []),
    l2pass_bridge_google                : (l2pass_bridge_google, 3, 'L2Pass google bridge', 0, []),
    nogem_bridge_google                 : (nogem_bridge_google, 3, 'nogem.app google bridge', 0, []),
    whale_bridge_google                 : (whale_bridge_google, 3, 'Whale google bridge', 0, []),
    merkly_nft_attack                   : (merkly_nft_attack, 3, 'Merkly NFT attack', 0, []),
    zerius_nft_attack                   : (zerius_nft_attack, 3, 'Zerius NFT attack', 0, []),
    l2pass_nft_attack                   : (l2pass_nft_attack, 3, 'L2Pass NFT attack', 0, []),
    nogem_nft_attack                    : (nogem_nft_attack, 3, 'nogem.app NFT attack', 0, []),
    whale_nft_attack                    : (whale_nft_attack, 3, 'Whale NFT attack', 0, []),
    gas_station_l2pass                  : (gas_station_l2pass, 3, 'L2Pass Gas Station', 0, []),
    filler_nogem                        : (filler_nogem, 3, 'nogem.app Filler', 0, []),
    check_in_owlto                      : (check_in_owlto, 2, 'Check-in Owlto', 0, [0]),
    send_message_dmail                  : (send_message_dmail, 2, 'Dmail message', 1, [3, 4, 8, 9, 11]),
    send_message_l2telegraph            : (send_message_l2telegraph, 2, 'L2Telegraph message', 0, []),
    bingx_transfer                      : (bingx_transfer, 2, 'BingX transfer', 0, []),
    transfer_eth                        : (transfer_eth, 2, 'Transfer ETH', 0, []),
    transfer_eth_to_myself              : (transfer_eth_to_myself, 2, 'Transfer ETH to myself', 0, []),
    withdraw_liquidity_maverick         : (withdraw_liquidity_maverick, 3, 'Maverick withdraw', 0, []),
    withdraw_liquidity_mute             : (withdraw_liquidity_mute, 3, 'Mute withdraw', 0, []),
    withdraw_liquidity_syncswap         : (withdraw_liquidity_syncswap, 3, 'SyncSwap withdraw', 0, []),
    withdraw_basilisk                   : (withdraw_basilisk, 3, 'Basilisk withdraw', 0, []),
    withdraw_eralend                    : (withdraw_eralend, 3, 'EraLend withdraw', 0, []),
    withdraw_reactorfusion              : (withdraw_reactorfusion, 3, 'ReactorFusion withdraw', 0, []),
    withdraw_zerolend                   : (withdraw_zerolend, 3, 'ZeroLend withdraw', 0, []),
    withdraw_layerbank                  : (withdraw_layerbank, 3, 'LayerBank withdraw', 0, []),
    withdraw_rocketsam                  : (withdraw_rocketsam, 3, 'RocketSam withdraw', 0, []),
    withdraw_moonwell                   : (withdraw_moonwell, 3, 'Moonwell withdraw', 0, []),
    withdraw_native_bridge              : (withdraw_native_bridge, 3, 'Native Bridge withdraw', 0, []),
    withdraw_seamless                   : (withdraw_seamless, 3, 'Seamless withdraw', 0, [0]),
    withdraw_usdbc_seamless             : (withdraw_usdbc_seamless, 3, 'Seamless USDbC withdraw', 0, [0]),
    withdraw_usdb_zerolend              : (withdraw_usdb_zerolend, 3, 'ZeroLend USDB withdraw', 0, [0]),
    wrap_abuser                         : (wrap_abuser, 2, 'Wrap Abuse =)', 0, []),
    collector_eth                       : (collector_eth, 4, 'Collect ETH from tokens', 0, []),
    okx_deposit                         : (okx_deposit, 5, 'OKX deposit', 0, []),
    bingx_deposit                       : (bingx_deposit, 5, 'Bingx deposit', 0, []),
    binance_deposit                     : (binance_deposit, 5, 'Binance deposit', 0, []),
    bitget_deposit                      : (bitget_deposit, 5, 'BitGet deposit', 0, []),
}


def get_func_by_name(module_name, help_message:bool = False):
    for k, v in AVAILABLE_MODULES_INFO.items():
        if k.__name__ == module_name:
            if help_message:
                return v[2]
            return v[0]


class RouteGenerator(Logger):
    def __init__(self, silent:bool = True):
        Logger.__init__(self)
        self.modules_names_const = [module.__name__ for module in list(AVAILABLE_MODULES_INFO.keys())]

        if GOOGLE_SHEET_URL != '' and not silent:
            self.gc: Client = service_account(filename=GSHEET_CONFIG)
            self.sh: Spreadsheet = self.gc.open_by_url(GOOGLE_SHEET_URL)
            self.ws: Worksheet = self.sh.worksheet(GOOGLE_SHEET_PAGE_NAME)
        else:
            self.gc, self.sh, self.ws = None, None, None
            self.w3 = AsyncWeb3()

    @staticmethod
    def classic_generate_route():
        route = []
        rpc = GLOBAL_NETWORK

        copy_route = copy.deepcopy(CLASSIC_ROUTES_MODULES_USING)

        if SHUFFLE_ROUTE:
            random.shuffle(copy_route)

        for i in copy_route:
            module_name = random.choice(i)
            if module_name is None:
                continue
            if ':' in module_name:
                module_name, rpc = module_name.split(':')

            module = get_func_by_name(module_name)
            if module:
                route.append(f"{module.__name__} {rpc}")
            else:
                raise SoftwareException(f'There is no module with the name "{module_name}" in the software.')
        return route

    def get_account_name_list(self):
        try:
            return self.ws.col_values(1)[1:]
        except Exception as error:
            self.logger_msg(None, None, f"Put data into 'GOOGLE_SHEET_URL' and 'service_accounts.json' first!", 'error')
            raise SoftwareException(f"{error}")

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

        if GLOBAL_NETWORK == 0:
            if not self.ws:
                raise SoftwareException('GLOBAL_NETWORK = 0 does not support classic routes')
            for module_name in modules_list_str:
                module_func = None
                module_name_symbol, module_path, module_type = module_name.split()

                if module_type == 'R':
                    if module_name_symbol == 'L':
                        module_func = l2pass_refuel_google
                    elif module_name_symbol == 'M':
                        module_func = merkly_refuel_google
                    elif module_name_symbol == 'W':
                        module_func = whale_refuel_google
                    elif module_name_symbol == 'Z':
                        module_func = zerius_refuel_google
                elif module_type == 'B':
                    if module_name_symbol == 'L':
                        module_func = l2pass_bridge_google
                    elif module_name_symbol == 'M':
                        module_func = merkly_bridge_google
                    elif module_name_symbol == 'W':
                        module_func = whale_bridge_google
                    elif module_name_symbol == 'Z':
                        module_func = zerius_bridge_google

                if module_func:
                    modules_list.append([module_func.__name__, module_name])
                else:
                    raise SoftwareException(f"That module does not exist in Google SpreadSheets")
        else:
            modules_list = []
            for module in modules_list_str:
                if module in self.modules_names_const:
                    modules_list.append(module)
                else:
                    raise SoftwareException(f"Module with name '{module}' does not exist in software features")

        return modules_list

    def get_data_for_batch(self, account_names:list, modules_list:list):
        wallet_list = self.get_account_name_list()
        batch_size = 200
        data_to_return = {}

        for i in range(0, len(account_names), batch_size):
            batch_account_names = account_names[i:i+batch_size]
            batch_data = self.get_data_for_single_batch(batch_account_names, wallet_list, modules_list)
            data_to_return.update(batch_data)

        return data_to_return

    def get_data_for_single_batch(self, batch_account_names:list, wallet_list:list, modules_list:list):
        ranges_for_sheet = []
        batch_data = {}
        data_to_return = {}
        col = 2 + len(modules_list)

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
        modules_list = self.get_modules_list()
        batch_data = self.get_data_for_batch(accounts_names, modules_list)
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
        elif GLOBAL_NETWORK in [4, 8]:
            collaterals_modules = [enable_collateral_layerbank, disable_collateral_layerbank]

        if GLOBAL_NETWORK != 0:
            try:
                for i in range(len(wallet_modules_statuses)):
                    if wallet_modules_statuses[i] in ["Not Started", "Error"]:
                        modules_to_work.append(modules_list[i])
            except IndexError:
                raise SoftwareException('Wrong GLOBAL_NETWORK or you missing the fields in your Google Sheet')

        else:
            for i in range(len(wallet_modules_statuses)):
                if wallet_modules_statuses[i] in ["Not Started", "Error"]:
                    modules_to_work.append([modules_list[i][0], modules_list[i][1]])

        excluded_modules = [module for module in EXCLUDED_MODULES if module in self.modules_names_const]

        if GLOBAL_NETWORK != 0:
            possible_modules = [module for module in modules_to_work if module not in excluded_modules]
        else:
            possible_modules = [module for module in modules_to_work if module[0] not in excluded_modules]

        want_count = len(modules_to_work) if ALL_MODULES_TO_RUN else random.choice(MODULES_COUNT)
        possible_count = min(want_count, len(possible_modules))

        possible_modules_data = []
        for module in possible_modules:
            if GLOBAL_NETWORK == 0:
                module_to_add = AVAILABLE_MODULES_INFO[get_func_by_name(module[0])], module[1]
            else:
                module_to_add = AVAILABLE_MODULES_INFO[get_func_by_name(module)]

            possible_modules_data.append(module_to_add)

        smart_route: list = random.sample(possible_modules_data, possible_count)

        dmails_count = random.randint(*DMAIL_COUNT)
        transfers_count = random.randint(*TRANSFER_COUNT)
        collaterals_count = random.randint(*COLLATERAL_COUNT)
        wraps_count = random.randint(*WRAPS_COUNT)

        if dmails_count:
            smart_route.extend([AVAILABLE_MODULES_INFO[send_message_dmail] for _ in range(dmails_count)])

        if collaterals_count and collaterals_modules:
            smart_route.extend([AVAILABLE_MODULES_INFO[random.choice(collaterals_modules)]
                                for _ in range(collaterals_count)])

        if transfers_count and transfers_modules:
            smart_route.extend([AVAILABLE_MODULES_INFO[random.choice(transfers_modules)]
                                for _ in range(transfers_count)])

        if wraps_count:
            smart_route.extend([AVAILABLE_MODULES_INFO[wrap_abuser] for _ in range(wraps_count)])

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
            elif GLOBAL_NETWORK in [4, 8]:
                smart_route.append(AVAILABLE_MODULES_INFO[withdraw_layerbank])
                smart_route.append(AVAILABLE_MODULES_INFO[withdraw_rocketsam])
            elif GLOBAL_NETWORK in [2, 3, 12]:
                smart_route.append(AVAILABLE_MODULES_INFO[withdraw_rocketsam])

        bridge_modules = [AVAILABLE_MODULES_INFO[bridge_across] if HELPERS_CONFIG['bridge_across'] else None,
                          AVAILABLE_MODULES_INFO[bridge_bungee] if HELPERS_CONFIG['bridge_bungee'] else None,
                          AVAILABLE_MODULES_INFO[bridge_rhino] if HELPERS_CONFIG['bridge_rhino'] else None,
                          AVAILABLE_MODULES_INFO[bridge_relay] if HELPERS_CONFIG['bridge_relay'] else None,
                          AVAILABLE_MODULES_INFO[bridge_owlto] if HELPERS_CONFIG['bridge_owlto'] else None,
                          AVAILABLE_MODULES_INFO[bridge_layerswap] if HELPERS_CONFIG['bridge_layerswap'] else None,
                          AVAILABLE_MODULES_INFO[bridge_orbiter] if HELPERS_CONFIG['bridge_orbiter'] else None,
                          AVAILABLE_MODULES_INFO[bridge_native] if HELPERS_CONFIG['bridge_native'] else None]

        bridge_to_add = [i for i in bridge_modules if i]

        if bridge_to_add:
            smart_route.append(random.choice(bridge_to_add))

        smart_route.append(AVAILABLE_MODULES_INFO[okx_withdraw] if HELPERS_CONFIG['okx_withdraw'] else None)
        smart_route.append(AVAILABLE_MODULES_INFO[bingx_withdraw] if HELPERS_CONFIG['bingx_withdraw'] else None)
        smart_route.append(AVAILABLE_MODULES_INFO[binance_withdraw] if HELPERS_CONFIG['binance_withdraw'] else None)
        smart_route.append(AVAILABLE_MODULES_INFO[bitget_withdraw] if HELPERS_CONFIG['bitget_withdraw'] else None)
        smart_route.append(AVAILABLE_MODULES_INFO[okx_deposit] if HELPERS_CONFIG['okx_deposit'] else None)
        smart_route.append(AVAILABLE_MODULES_INFO[bingx_deposit] if HELPERS_CONFIG['bingx_deposit'] else None)
        smart_route.append(AVAILABLE_MODULES_INFO[binance_deposit] if HELPERS_CONFIG['binance_deposit'] else None)
        smart_route.append(AVAILABLE_MODULES_INFO[bitget_deposit] if HELPERS_CONFIG['bitget_deposit'] else None)
        smart_route.append(AVAILABLE_MODULES_INFO[collector_eth] if HELPERS_CONFIG['collector_eth'] else None)
        smart_route.append(
            AVAILABLE_MODULES_INFO[make_balance_to_average] if HELPERS_CONFIG['make_balance_to_average'] else None)

        if INCLUDED_MODULES:
            for module in INCLUDED_MODULES:
                module_func = get_func_by_name(module)
                if module_func:
                    smart_route.append(AVAILABLE_MODULES_INFO[module_func])

        random.shuffle(smart_route)

        if GLOBAL_NETWORK != 0:
            default_rpc = GLOBAL_NETWORK
            smart_route_with_priority = [
                f"{i[0].__name__} {default_rpc}" for i in sorted(list(filter(None, smart_route)), key=lambda x: x[1])
            ]
        else:
            smart_route_with_priority = [(i[0][0].__name__, i[1]) for i in list(filter(None, smart_route))]

        self.smart_routes_json_save(account_name, smart_route_with_priority)

    @staticmethod
    def sort_classic_route(route):
        modules_dependents = {
            'okx_withdraw': 0,
            'bingx_withdraw': 0,
            'binance_withdraw': 0,
            'bitget_withdraw': 0,
            'make_balance_to_average': 1,
            'bridge_rhino': 1,
            'bridge_layerswap': 1,
            'bridge_nitro': 1,
            'bridge_orbiter': 1,
            'bridge_across': 1,
            'bridge_owlto': 1,
            'bridge_relay': 1,
            'bridge_native': 1,
            'bridge_zora': 1,
            'collector_eth': 3,
            'okx_deposit': 4,
            'bingx_deposit': 4,
            'binance_deposit': 4,
            'bitget_deposit': 4,
            'okx_deposit_l0': 4,
        }

        new_route = []
        classic_route = []
        for module_name in route:
            if module_name in modules_dependents:
                classic_route.append((module_name, modules_dependents[module_name]))
            else:
                new_route.append((module_name, 2))

        random.shuffle(new_route)
        classic_route.extend(new_route)
        route_with_priority = [module[0] for module in sorted(classic_route, key=lambda x: x[1])]

        deposit_modules = [
            'deposit_basilisk',
            'deposit_eralend',
            'deposit_reactorfusion',
            'deposit_zerolend',
            'deposit_usdb_zerolend',
            'deposit_layerbank',
            'deposit_rocketsam',
            'deposit_moonwell',
            'deposit_seamless',
            'deposit_usdbc_seamless',
            'deposit_abracadabra',
        ]

        if CLASSIC_WITHDRAW_DEPENDENCIES:
            new_route_with_dep = []
            for module_info in route_with_priority:
                module_name, rpc = module_info.split(" ")
                new_route_with_dep.append(module_info)

                if module_name in deposit_modules:
                    withdraw_module_name = module_name.replace('deposit', 'withdraw')
                    withdraw_module = get_func_by_name(withdraw_module_name)
                    new_route_with_dep.append(f"{withdraw_module.__name__} {rpc}")
        else:
            new_route_with_dep = route_with_priority

        return new_route_with_dep

    def classic_routes_json_save(self):
        clean_progress_file()
        with open('./data/services/wallets_progress.json', 'w') as file:
            accounts_data = {}
            for account_name in ACCOUNT_NAMES:
                if isinstance(account_name, (str, int)):
                    classic_route = self.classic_generate_route()
                    if SHUFFLE_ROUTE:
                        classic_route = self.sort_classic_route(route=classic_route)
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
            "route": ([" ".join(item) for item in route] if isinstance(route[0], tuple) else route) if route else []
        }

        with open(progress_file_path, 'w') as file:
            json.dump(data, file, indent=4)

        self.logger_msg(
            None, None,
            f'Successfully generated smart routes for {account_name}', 'success')
