import asyncio
import sys

from config import TITLE
from termcolor import cprint
from modules import txchecker
from questionary import Choice, select
from utils.modules_runner import Runner
from utils.route_generator import RouteGenerator
from utils.tools import create_okx_withdrawal_list


def are_you_sure(module):
    answer = select(
        '\n ⚠️⚠️⚠️ THAT ACTION DELETE ALL PREVIOUS DATA, continue? ⚠️⚠️⚠️ \n',
        choices=[
            Choice("❌ NO", 'main'),
            Choice("✅ YES", 'module'),
        ],
        qmark='☢️',
        pointer='👉'
    ).ask()
    print()
    if answer == 'main':
        main()
    else:
        module()


def get_module_name():
    answer = select(
        'What module do you need?\n',
        choices=[
            Choice("⚫ Withdraw OKX", 'okx_withdraw'),
            Choice("🔵 Bridge on txSync", 'bridge_txsync'),
            Choice("🔵 Bridge on Rhino.fi", 'bridge_rhino'),
            Choice("🔵 Bridge on LayerSwap", 'bridge_layerswap'),
            Choice("🔵 Bridge on Orbiter", 'bridge_orbiter'),
            Choice("🔴 Refuel on Merkly", 'refuel_merkly'),
            Choice("🔴 Refuel on Bungee", 'refuel_bungee'),
            Choice("🟢 Swap on iZumi", 'swap_izumi'),
            Choice("🟢 Swap on Maverick", 'swap_maverick'),
            Choice("🟢 Swap on Pancake", 'swap_pancake'),
            Choice("🟢 Swap on 1INCH", 'swap_oneinch'),
            Choice("🟢 Swap on Odos", 'swap_odos'),
            Choice("🟢 Swap on Rango", 'swap_rango'),
            Choice("🟢 Swap on WooFi", 'swap_woofi'),
            Choice("🟢 Swap on SyncSwap", 'swap_syncswap'),
            Choice("🟢 Swap on OpenOcean", 'swap_openocean'),
            Choice("🟢 Swap on zkSwap", 'swap_zkswap'),
            Choice("🟢 Swap on Mute", 'swap_mute'),
            Choice("🟢 Swap on SpaceFi", 'swap_spacefi'),
            Choice("🟢 Swap on VeSync", 'swap_vesync'),
            Choice("🟢 Swap on XYfinance", 'swap_xyfinance'),
            Choice("🟣 Add liquidity on Mute", 'add_liquidity_mute'),
            Choice("🟣 Add liquidity on Maverick", 'add_liquidity_maverick'),
            Choice("🟣 Add liquidity on SyncSwap", 'add_liquidity_syncswap'),
            Choice("🟣 Withdraw liquidity from Mute", 'withdraw_liquidity_mute'),
            Choice("🟣 Withdraw liquidity from Maverick", 'withdraw_liquidity_maverick'),
            Choice("🟣 Withdraw liquidity from SyncSwap", 'withdraw_liquidity_syncswap'),
            Choice("🟣 Deposit on EraLend", 'deposit_eralend'),
            Choice("🟣 Deposit on ZeroLend", 'deposit_zerolend'),
            Choice("🟣 Deposit on Basilisk", 'deposit_basilisk'),
            Choice("🟣 Deposit on Reactorfusion", 'deposit_reactorfusion'),
            Choice("🟣 Withdraw from EraLend", 'withdraw_eralend'),
            Choice("🟣 Withdraw from ZeroLend", 'withdraw_zerolend'),
            Choice("🟣 Withdraw from Basilisk", 'withdraw_basilisk'),
            Choice("🟣 Withdraw from Reactorfusion", 'withdraw_reactorfusion'),
            Choice("🟠 Enable collateral on Eralend", 'enable_collateral_eralend'),
            Choice("🟠 Enable collateral on ZeroLend", 'enable_collateral_zerolend'),
            Choice("🟠 Enable collateral on Basilisk", 'enable_collateral_basilisk'),
            Choice("🟠 Enable collateral on Reactorfusion", 'enable_collateral_reactorfusion'),
            Choice("🟠 Disable collateral on Eralend", 'disable_collateral_eralend'),
            Choice("🟠 Disable collateral on ZeroLend", 'disable_collateral_zerolend'),
            Choice("🟠 Disable collateral on Basilisk", 'disable_collateral_basilisk'),
            Choice("🟠 Disable collateral on Reactorfusion", 'disable_collateral_reactorfusion'),
            Choice("🟠 Deploy contract on zkSync", 'deploy_contract'),
            Choice("🟡 Mint Citizen ID and Guardian NFT on Tevaera", 'mint_tevaera'),
            Choice("🟡 Bridge NFT on Zerius", 'bridge_zerius'),
            Choice("🟡 Mint NFT on Zerius", 'mint_zerius'),
            Choice("🟡 Mint free NFT on MailZero", 'mint_mailzero'),
            Choice("🟡 Mint domain on Era Name Service. 0.003 ETH", 'mint_domain_ens'),
            Choice("🟡 Mint domain on zkSync Name Service. 0.0 ETH", 'mint_domain_zns'),
            Choice("🟡 Mint and bridge NFT on L2Telegraph", 'mint_and_bridge_l2telegraph'),
            Choice("🟡 Create safe on chain", 'create_safe'),
            Choice("🟡 Create NFT collection on OmniSea", 'create_omnisea'),
            Choice("⚪ Send message on Dmail", 'send_message_dmail'),
            Choice("⚪ Send message on L2Telegraph", 'send_message_l2telegraph'),
            Choice("⚪ Wrap ETH", 'wrap_eth'),
            Choice("⚪ Unwrap ETH", 'unwrap_eth'),
            Choice("⚪ Transfer ETH to random address", 'transfer_eth'),
            Choice("⚪ Transfer ETH to your own address", 'transfer_eth_to_myself'),
            Choice("🔵 Withdraw from Era on txSync", 'withdraw_txsync'),
            Choice("⚫ Deposit OKX", 'okx_deposit'),
            Choice("⚫ Collect funds from subs on OKX", 'okx_collect_from_sub'),
            Choice('Back to menu', 'main')
        ],
        qmark='🛠️',
        pointer='👉'
    ).ask()
    return answer


def main():
    print(TITLE)
    cprint(f'\n❤️ Subscribe to my channel: https://t.me/askaer', 'light_cyan', attrs=["blink"])
    cprint(f'\n💵 Donate (Any EVM) --> 0x000000a679C2FB345dDEfbaE3c42beE92c0Fb7A5\n', 'light_cyan')

    while True:
        answer = select(
            'What do you want to do?',
            choices=[
                Choice("🤖 Start running smart routes *(c)GOOGLE POWERED", 'smart_routes_run'),
                Choice("🚀 Start running classic routes for each wallet", 'classic_routes_run'),
                Choice("📄 Generate classic-route for each wallet", 'classic_routes_gen'),
                Choice("💾 Create and safe OKX withdrawal file", 'create_okx_list'),
                Choice("✅ Check the connection of each proxy", 'check_proxy'),
                Choice("👈 Choose one module to run", 'run_one_module'),
                Choice("📊 Get TX stats for all wallets", 'tx_stat'),
                Choice('❌ Exit', "exit")
            ],
            qmark='🛠️',
            pointer='👉'
        ).ask()

        runner = Runner()

        if answer == 'check_proxy':
            print()
            asyncio.run(runner.check_proxies_status())
            print()
        elif answer == 'smart_routes_run':
            print()
            asyncio.run(runner.run_accounts(smart_route=True))
            print()
        elif answer == 'classic_routes_run':
            print()
            asyncio.run(runner.run_accounts(smart_route=False))
            print()
        elif answer == 'create_okx_list':
            print()
            create_okx_withdrawal_list()
            print()
        elif answer == 'run_one_module':
            print()
            module_name = get_module_name()
            if module_name == 'main':
                main()
            asyncio.run(runner.run_module(module_name))
            print()
        elif answer == 'tx_stat':
            print()
            asyncio.run(txchecker.main())
            print()
        elif answer == 'classic_routes_gen':
            generator = RouteGenerator()
            are_you_sure(generator.routes_json_save)
        elif answer == 'exit':
            sys.exit()
        else:
            print()
            answer()
            print()


if __name__ == "__main__":
    main()
