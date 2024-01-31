import asyncio
import sys

from config import TITLE
from termcolor import cprint
from modules import txchecker
from questionary import Choice, select

from modules.interfaces import SoftwareException
from utils.modules_runner import Runner
from utils.route_generator import RouteGenerator
from utils.tools import create_cex_withdrawal_list, drop_date, clean_stark_file, check_progress_file


def when():
    cprint(f"{drop_date()}", color='light_red', attrs=["blink"])


def are_you_sure(module=None, gen_route: bool = False):
    if gen_route or check_progress_file():
        answer = select(
            '\n ⚠️⚠️⚠️ THAT ACTION WILL DELETE ALL PREVIOUS PROGRESS FOR CLASSIC-ROUTES, continue? ⚠️⚠️⚠️ \n',
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
            if module:
                module()


def main():
    print(TITLE)
    cprint(f'\n❤️ My channel for latest updates: https://t.me/askaer\n', 'light_cyan', attrs=["blink"])
    try:
        while True:
            answer = select(
                'What do you want to do?',
                choices=[
                    Choice("🤖 Start running smart routes (c)GOOGLE POWERED", 'smart_routes_run'),
                    Choice("🚀 Start running classic routes for each wallet", 'classic_routes_run'),
                    Choice("📄 Generate classic-route for each wallet", 'classic_routes_gen'),
                    Choice("💾 Create and safe CEX withdrawal file", 'create_cex_list'),
                    Choice("✅ Check the connection of each proxy", 'check_proxy'),
                    Choice("📊 Get TX stats for all wallets", 'tx_stat'),
                    Choice("⏰ WHEN?", 'when'),
                    Choice('❌ Exit', "exit")
                ],
                qmark='🛠️',
                pointer='👉'
            ).ask()

            runner = Runner()
            clean_stark_file()

            if answer == 'check_proxy':
                print()
                asyncio.run(runner.check_proxies_status())
                print()
            elif answer == 'smart_routes_run':
                print()
                are_you_sure()
                asyncio.run(runner.run_accounts(smart_route=True))
                print()
            elif answer == 'classic_routes_run':
                print()
                asyncio.run(runner.run_accounts(smart_route=False))
                print()
            elif answer == 'create_cex_list':
                print()
                create_cex_withdrawal_list()
                print()
            elif answer == 'tx_stat':
                print()
                asyncio.run(txchecker.main())
                print()
            elif answer == 'classic_routes_gen':
                generator = RouteGenerator()
                are_you_sure(generator.classic_routes_json_save, gen_route=True)
            elif answer == 'when':
                print()
                when()
                print()
            elif answer == 'exit':
                sys.exit()
            elif answer is not None:
                print()
                answer()
                print()
            else:
                raise KeyboardInterrupt
    except KeyboardInterrupt:
        cprint(f'\nQuick software shutdown by <ctrl + C>', color='light_yellow')
        sys.exit()

    except SoftwareException as error:
        cprint(f'\n{error}', color='light_red')
        sys.exit()


if __name__ == "__main__":
    main()
