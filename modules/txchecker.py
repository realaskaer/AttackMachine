import csv
import requests
import aiohttp
import asyncio
import pandas as pd
from termcolor import cprint
from web3 import AsyncWeb3
from prettytable import PrettyTable
from datetime import datetime
from collections import defaultdict


API_URL = "https://block-explorer-api.mainnet.zksync.io"

FILTER_SYMBOLS = ['ETH', 'USDT', 'USDC', 'BUSD']
ALL_SYMBOLS = [
    'USDT', 'USDC', 'BUSD', 'DAI', 'ZKUSD', 'CEBUSD', 'WETH', 'LUSD', 'USD+', 'ibETH', 'WETH', 'ibUSDC', 'ETH'
]

FIELDS = [
    '#', 'Wallet', 'ETH', 'USDC', 'USDT', 'BUSD', 'TX Count', 'Volume', 'Contracts',
    'Bridge to/from', 'Days/Weeks/Months', 'First/Last tx', 'Total gas spent'
]

table = PrettyTable()
table.field_names = FIELDS

def get_eth_price():
    url = 'https://api.coingecko.com/api/v3/simple/price'

    params = {
        'ids': 'ethereum',
        'vs_currencies': 'usd'
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        return data['ethereum']['usd']
    else:
        cprint(f'Bad request to Binance API: {response.status_code}', 'light_red')


ETH_PRICE = get_eth_price()


async def get_wallet_balance(session, wallet):
    balance = defaultdict(float)

    async with session.get(f"{API_URL}/address/{wallet}") as response:
        data = await response.json()

    balances = data.get('balances', {})

    for balance_data in balances.values():
        token_data = balance_data.get('token', None)
        if token_data is None:
            pass
        else:
            token_symbol = token_data.get('symbol', None)
            if token_symbol in FILTER_SYMBOLS:
                balance[token_symbol] = float(balance_data['balance']) / (10 ** balance_data['token']['decimals'])

    return balance


async def get_transaction_data(session, wallet):
    unique_days, unique_weeks, unique_months, unique_contracts = set(), set(), set(), set()
    total_gas_used, total_value, bridge_to, bridge_from = 0, 0, 0, 0
    first_tx_date, last_tx_date = '', ''
    txs = []

    page = 1
    while True:

        params = {
            'address': wallet,
            'page': page,
            'limit': 100
        }

        async with session.get(f"{API_URL}/transactions", params=params) as response:
            data = await response.json()

            items = data.get('items', [])
            meta = data.get('meta', {})
            txs.extend([tx for tx in items if tx['from'] == wallet])

            if meta['currentPage'] == meta['totalPages'] or meta['totalItems'] == 0:
                break
            page += 1

    for tx in txs:
        date = datetime.strptime(tx['receivedAt'], "%Y-%m-%dT%H:%M:%S.%fZ")
        unique_days.add(date.strftime("%Y-%m-%d"))
        unique_weeks.add(f"{date.year}-{date.strftime('%U')}")
        unique_months.add(f"{date.year}-{date.strftime('%m')}")
        unique_contracts.add(tx['to'])
        total_gas_used += int(tx['fee'], 16) / (10 ** 18)

    if txs:
        first_tx_date = datetime.strptime(txs[-1]['receivedAt'], "%Y-%m-%dT%H:%M:%S.%fZ").strftime('%Y-%m-%d')
        last_tx_date = datetime.strptime(txs[0]['receivedAt'], "%Y-%m-%dT%H:%M:%S.%fZ").strftime('%Y-%m-%d')

    page_transfers = 1
    while True:

        params = {
            'limit': 100,
            'page': page_transfers
        }

        async with session.get(f"{API_URL}/address/{wallet}/transfers", params=params) as response:
            data = await response.json()
            items = data.get('items', [])
            meta = data.get('meta', {})

            for transfer in items:
                if transfer['type'] == 'deposit' and transfer['from'] == wallet == transfer['to']:
                    bridge_to += 1

                if transfer['type'] == 'withdrawal' and transfer['from'] == wallet == transfer['to']:
                    bridge_from += 1

                if transfer['token'] and transfer['from'] == wallet:
                    if transfer['token']['symbol'] in ALL_SYMBOLS:
                        amount = int(transfer['amount']) / (10 ** transfer['token']['decimals'])

                        if transfer['token']['symbol'] in ['ETH', 'WETH']:
                            total_value += amount * ETH_PRICE
                        else:
                            total_value += amount

        if meta['currentPage'] == meta['totalPages'] or meta['totalItems'] == 0:
            break
        page_transfers += 1

    data = {
        'tx_count': len(txs) - 1,
        'bridge_to': bridge_to,
        'bridge_from': bridge_from,
        'total_value': total_value,
        'last_tx_date': last_tx_date,
        'first_tx_date': first_tx_date,
        'total_gas_used': total_gas_used,
        'unique_days': len(unique_days),
        'unique_weeks': len(unique_weeks),
        'unique_months': len(unique_months),
        'unique_contracts': len(unique_contracts),
    }

    return data


async def fetch_wallet_data(session, wallet, index):
    balance = await get_wallet_balance(session, wallet)
    txs_data = await get_transaction_data(session, wallet)
    first_tx, last_tx = (txs_data['first_tx_date'], txs_data['last_tx_date']) if txs_data['tx_count'] else ('—', '—')
    dwm_date = f'{txs_data['unique_days']} / {txs_data['unique_weeks']} / {txs_data['unique_months']}'

    return {
        '#'                     : index + 1,
        'Wallet'                : f'{wallet[:10]}...{wallet[-10:]}',
        'ETH'                   : f"{balance['ETH']:.4f} (${(balance['ETH'] * ETH_PRICE):.2f})",
        'USDC'                  : f"{balance['USDC']:.2f}",
        'USDT'                  : f"{balance['USDT']:.2f}",
        'BUSD'                  : f"{balance['BUSD']:.2f}",
        'TX Count'              : txs_data['tx_count'],
        'Volume'                : f"${txs_data['total_value']:.2f}",
        'Contracts'             : txs_data['unique_contracts'],
        'Bridge to/from'        : f"{txs_data['bridge_to']} / {txs_data['bridge_from']}",
        'Days/Weeks/Months'     : dwm_date,
        'First/Last tx'         : f"{first_tx} / {last_tx}",
        'Total gas spent'       : f"{txs_data['total_gas_used']:.4f} (${(txs_data['total_gas_used'] * ETH_PRICE):.2f})"
    }


def save_to_csv(wallet_data):
    with open('./data/wallets_stats.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(FIELDS)
        for data in wallet_data:
            table.add_row(data.values())
            writer.writerow([data[key] for key in FIELDS])


async def main():
    async with aiohttp.ClientSession() as session:
        with open('./data/wallets.txt') as file:
            wallets = [AsyncWeb3().eth.account.from_key(row.rstrip()).address for row in file.readlines()]

        tasks = [fetch_wallet_data(session, wallet, index) for index, wallet in enumerate(wallets, 0)]
        wallet_data = await asyncio.gather(*tasks)

    save_to_csv(wallet_data)
    cprint('Data successfully load to /data/wallets_stats.xlsx (Excel format)\n',
           'light_yellow', attrs=["blink"])
    await asyncio.sleep(1)
    xlsx_data = pd.read_csv('./data/wallets_stats.csv')
    xlsx_data.to_excel('./data/wallets_stats.xlsx')
    print(table)
