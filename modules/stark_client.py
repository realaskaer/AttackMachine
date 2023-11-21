import asyncio
import json
import random

from starknet_py.contract import Contract
from starknet_py.net.account.account import Account
from starknet_py.hash.address import compute_address
from starknet_py.net.client_errors import ClientError
from starknet_py.cairo.felt import decode_shortstring
from starknet_py.net.models.chains import StarknetChainId
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.hash.selector import get_selector_from_name
from starknet_py.net.signer.stark_curve_signer import KeyPair
from starknet_py.net.client_models import Call

from aiohttp import ClientSession
from aiohttp_socks import ProxyConnector
from modules import Logger
from utils.networks import Network
from config import (
    TOKENS_PER_CHAIN,
    RHINO_CHAIN_INFO,
    ORBITER_CHAINS_INFO,
    LAYERSWAP_CHAIN_NAME,
    ARGENT_IMPLEMENTATION_CLASS_HASH_NEW,
    BRAAVOS_PROXY_CLASS_HASH, BRAAVOS_IMPLEMENTATION_CLASS_HASH, ARGENT_PROXY_CLASS_HASH,
    ARGENT_IMPLEMENTATION_CLASS_HASH, ZKLEND_CONTRACTS, NOSTRA_CONTRACTS
)

from settings import (
    USE_PROXY,
    GAS_MULTIPLIER,
    UNLIMITED_APPROVE,
    AMOUNT_PERCENT,
    MIN_BALANCE,
    DEX_LP_AMOUNT,
    LANDING_AMOUNT,
    LAYERSWAP_AMOUNT,
    LAYERSWAP_CHAIN_ID_TO,
    LAYERSWAP_REFUEL,
    ORBITER_AMOUNT,
    ORBITER_CHAIN_ID_TO,
    RHINO_AMOUNT,
    RHINO_CHAIN_ID_TO, PRICE_IMPACT
)


class StarknetClient(Logger):
    def __init__(self, account_name: int, private_key: str, network: Network, proxy: None | str = None):
        super().__init__()
        self.network = network
        self.token = network.token
        self.explorer = network.explorer
        self.chain_id = StarknetChainId.MAINNET
        self.proxy = f"http://{proxy}" if proxy else ""
        self.proxy_init = proxy

        key_pair = KeyPair.from_private_key(private_key)
        self.key_pair = key_pair
        self.session = self.get_proxy_for_account(self.proxy)
        self.w3 = FullNodeClient(node_url=random.choice(network.rpc), session=self.session)

        self.account_name = account_name
        self.private_key = private_key
        self.min_amount_eth_on_balance = MIN_BALANCE
        self.account = None
        self.address = None
        self.WALLET_TYPE = None
        self.info = None

    async def initialize_account(self):
        self.account, self.address, self.WALLET_TYPE = await self.get_wallet_auto(self.w3, self.key_pair,
                                                                                  self.account_name)

        self.account.ESTIMATED_FEE_MULTIPLIER = GAS_MULTIPLIER
        self.info = f'[{self.account_name}] {hex(self.account.address)} | {self.network.name} |'

    async def get_wallet_auto(self, w3, key_pair, account_name):
        last_data = await self.check_stark_data_file(account_name)
        if last_data:
            address, wallet_type = last_data['address'], last_data['address']
            account = Account(client=w3, address=address, key_pair=key_pair, chain=StarknetChainId.MAINNET)
            return account, address, wallet_type

        possible_addresses = [(self.get_argent_address(key_pair, 1), 0),
                              (self.get_braavos_address(key_pair), 1),
                              (self.get_argent_address(key_pair, 0), 0)]

        for address, wallet_type in possible_addresses:
            account = Account(client=w3, address=address, key_pair=key_pair, chain=StarknetChainId.MAINNET)
            try:
                if await account.client.get_class_hash_at(address):
                    await self.save_stark_data_file(account_name, address, wallet_type)
                    return account, address, wallet_type
            except ClientError:
                pass

        self.logger_msg(None, None, f'Account name: "{account_name}" has no balance', 'warning')
        raise RuntimeError(f"Account name: '{account_name}' has not deployed")

    @staticmethod
    def get_proxy_for_account(proxy):
        if USE_PROXY and proxy != "":
            return ClientSession(connector=ProxyConnector.from_url(f"{proxy}"))
        return None

    @staticmethod
    async def check_stark_data_file(account_name):
        bad_progress_file_path = './data/services/stark_data.json'
        try:
            with open(bad_progress_file_path, 'r') as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}

        if account_name in data:
            return data[account_name]

    @staticmethod
    async def save_stark_data_file(account_name, address, wallet_type):
        bad_progress_file_path = './data/services/stark_data.json'
        try:
            with open(bad_progress_file_path, 'r') as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}

        data[account_name] = {
            'address': address,
            'wallet_type': wallet_type
        }

        with open(bad_progress_file_path, 'w') as file:
            json.dump(data, file, indent=4)

    @staticmethod
    def get_braavos_address(key_pair) -> int:
        selector = get_selector_from_name("initializer")
        call_data = [key_pair.public_key]

        return compute_address(
            class_hash=BRAAVOS_PROXY_CLASS_HASH,
            constructor_calldata=[BRAAVOS_IMPLEMENTATION_CLASS_HASH, selector, len(call_data), *call_data],
            salt=key_pair.public_key
        )

    @staticmethod
    def get_argent_address(key_pair, cairo_version) -> int:
        selector = get_selector_from_name("initialize")
        call_data = [key_pair.public_key, 0]

        if cairo_version:
            proxy_class_hash = ARGENT_IMPLEMENTATION_CLASS_HASH_NEW
            constructor_calldata = call_data
        else:
            proxy_class_hash = ARGENT_PROXY_CLASS_HASH
            constructor_calldata = [ARGENT_IMPLEMENTATION_CLASS_HASH, selector, len(call_data), *call_data]

        return compute_address(
            class_hash=proxy_class_hash,
            constructor_calldata=constructor_calldata,
            salt=key_pair.public_key
        )

    @staticmethod
    def round_amount(min_amount: float, max_amount:float) -> float:
        decimals = max(len(str(min_amount)) - 1, len(str(max_amount)) - 1)
        return round(random.uniform(min_amount, max_amount), decimals)

    @staticmethod
    def get_normalize_error(error):
        if 'message' in error.args[0]:
            error = error.args[0]['message']
        return error

    async def get_decimals(self, token_name:str):
        contract = TOKENS_PER_CHAIN[self.network.name][token_name]
        return (await self.account.client.call_contract(self.prepare_call(contract, 'decimals')))[0]

    async def get_normalize_amount(self, token_name, amount_in_wei):
        decimals = await self.get_decimals(token_name)

        return float(amount_in_wei / 10 ** decimals)

    async def get_smart_amount(self, settings:tuple, token_name:str = 'ETH'):
        if isinstance(settings[0], str):
            _, amount, _ = await self.get_token_balance(token_name)
            percent = round(random.uniform(int(settings[0]), int(settings[1]))) / 100
            amount = round(amount * percent, 6)

        else:
            amount = self.round_amount(*settings)

        return amount

    async def price_impact_defender(self, from_token_name, from_token_amount,
                                    to_token_name, to_token_amount_in_wei):

        to_token_amount = await self.get_normalize_amount(to_token_name, to_token_amount_in_wei)

        amount1_in_usd = (await self.get_token_price(from_token_name)) * from_token_amount
        amount2_in_usd = (await self.get_token_price(to_token_name)) * to_token_amount
        price_impact = 100 - (amount2_in_usd / amount1_in_usd) * 100

        if price_impact > PRICE_IMPACT:
            raise RuntimeError(
                f'DEX price impact > your wanted impact | DEX impact: {price_impact:.3}% > Your impact {PRICE_IMPACT}%')

    async def get_bridge_data(self, chain_from_id:int, _, __, module_name:str):
        if module_name == 'Rhino':
            source_chain = RHINO_CHAIN_INFO[chain_from_id]
            destination_chain = RHINO_CHAIN_INFO[random.choice(RHINO_CHAIN_ID_TO)]
            amount = await self.get_smart_amount(RHINO_AMOUNT)

            return source_chain, destination_chain, amount

        elif module_name == 'LayerSwap':
            source_chain = LAYERSWAP_CHAIN_NAME[chain_from_id]
            destination_chain = LAYERSWAP_CHAIN_NAME[random.choice(LAYERSWAP_CHAIN_ID_TO)]
            refuel = LAYERSWAP_REFUEL
            amount = await self.get_smart_amount(LAYERSWAP_AMOUNT)

            return source_chain, destination_chain, amount, refuel

        elif module_name == 'Orbiter':
            source_chain = ORBITER_CHAINS_INFO[chain_from_id]
            destination_chain = ORBITER_CHAINS_INFO[random.choice(ORBITER_CHAIN_ID_TO)]
            amount = await self.get_smart_amount(ORBITER_AMOUNT)

            return source_chain, destination_chain, amount

    async def get_landing_data(self, class_name:str, deposit:bool = False):
        landing_token_contracts = NOSTRA_CONTRACTS if class_name == 'Nostra' else ZKLEND_CONTRACTS

        token_list = list(TOKENS_PER_CHAIN[self.network.name].items())
        random.shuffle(token_list)

        for token_name, token_contract in token_list:
            landing_token_contract = landing_token_contracts[token_name]

            landing_balance = (await self.account.client.call_contract(self.prepare_call(
                contract_address=landing_token_contract,
                selector_name='balanceOf',
                calldata=[self.address]
            )))[0]

            if deposit:
                account_balance = (await self.account.client.call_contract(self.prepare_call(
                    contract_address=token_contract,
                    selector_name='balanceOf',
                    calldata=[self.address]
                )))[0]

                amount_to_deposit = await self.get_smart_amount(LANDING_AMOUNT, token_name)
                amount_to_deposit_usd = amount_to_deposit

                if token_name != 'ETH':
                    eth_vs_token_price = await self.get_token_price(token_name, 'eth')
                    amount_to_deposit_usd = round(amount_to_deposit / eth_vs_token_price, 3)
                amount_to_deposit_usd_in_wei = int(amount_to_deposit_usd * 10 ** (await self.get_decimals(token_name)))

                if account_balance > amount_to_deposit:
                    return token_name, token_contract, amount_to_deposit_usd, amount_to_deposit_usd_in_wei

            else:
                landing_withdraw_data = [token_name, token_contract]

                if landing_balance > 0:
                    if class_name == 'Nostra':
                        landing_withdraw_data.append(landing_balance)
                    return landing_withdraw_data
        if deposit:
            raise RuntimeError(f'Insufficient balance on account!')
        raise RuntimeError(f'Insufficient balance on {class_name} pools!')

    async def check_and_get_eth_for_deposit(self, settings:tuple = None) -> [float, int]:
        from functions import swap_avnu
        data = await self.get_auto_amount(token_name_search='ETH')

        amount = await self.get_smart_amount(settings if settings else LANDING_AMOUNT)
        amount_in_wei = int(amount * 10 ** 18)

        if data is False:
            self.logger.warning(f'{self.info} Not enough ETH! Launching swap module')

            await asyncio.sleep(1)
            await swap_avnu(self.account_name, self.private_key, self.network, self.proxy_init, help_deposit=True)
        else:
            _, _, amount, amount_in_wei = data

        return amount, amount_in_wei

    async def check_and_get_eth_for_liquidity(self) -> [float, int]:
        from functions import swap_avnu

        eth_balance_in_wei, eth_balance, _ = await self.get_token_balance('ETH')
        amount_from_settings = await self.get_smart_amount(DEX_LP_AMOUNT)
        amount_from_settings_in_wei = int(amount_from_settings * 10 ** 18)

        await asyncio.sleep(1)
        if eth_balance < amount_from_settings:
            self.logger.warning(f'{self.info} Not enough ETH! Launching swap module')
            await asyncio.sleep(1)
            await swap_avnu(self.account_name, self.private_key, self.network, self.proxy_init,
                            help_deposit=True, amount_to_help=amount_from_settings)

        return amount_from_settings, amount_from_settings_in_wei

    async def get_auto_amount(self, token_name_search:str = None, class_name:str = None) -> [str, float, int]:

        wallet_balance = {k: await self.get_token_balance(k, False)
                          for k, v in TOKENS_PER_CHAIN[self.network.name].items()}
        valid_wallet_balance = {k: v[1] for k, v in wallet_balance.items() if v[0] != 0}
        eth_price = await self.get_token_price('ethereum')

        if 'ETH' in valid_wallet_balance:
            valid_wallet_balance['ETH'] = valid_wallet_balance['ETH'] * eth_price

        if sum(valid_wallet_balance.values()) > self.min_amount_eth_on_balance * eth_price:

            valid_wallet_balance = {k: round(v, 7) for k, v in valid_wallet_balance.items()}

            biggest_token_balance_name = max(valid_wallet_balance, key=lambda x: valid_wallet_balance[x])

            if token_name_search == 'ETH' and biggest_token_balance_name != 'ETH':
                return False

            amount_from_token_on_balance = wallet_balance[biggest_token_balance_name][1]
            amount_from_token_on_balance_in_wei = wallet_balance[biggest_token_balance_name][0]

            token_names_list = list(filter(lambda token_name: token_name != biggest_token_balance_name,
                                           TOKENS_PER_CHAIN[self.network.name].keys()))

            random_to_token_name = random.choice(token_names_list)

            percent = 1
            if biggest_token_balance_name == 'ETH':
                percent = round(random.uniform(*AMOUNT_PERCENT)) / 100

            amount = round(amount_from_token_on_balance * percent, 7)
            amount_in_wei = round(amount_from_token_on_balance_in_wei * percent)

            return biggest_token_balance_name, random_to_token_name, amount, amount_in_wei

        else:
            raise RuntimeError('Insufficient balance on account!')

    async def check_wallet_type(self):
        class_hash = await self.account.client.get_class_hash_at(self.account.address)
        if class_hash == int(BRAAVOS_PROXY_CLASS_HASH, 16):
            return 'braavos', 1
        return 'argent', 0

    async def get_contract(self, contract_address: str, proxy_config: bool = False):
        return await Contract.from_address(address=contract_address, provider=self.account, proxy_config=proxy_config)

    @staticmethod
    def prepare_call(contract_address:int, selector_name:str, calldata:list = None):
        if calldata is None:
            calldata = []
        return Call(
            to_addr=contract_address,
            selector=get_selector_from_name(selector_name),
            calldata=[int(data) for data in calldata],
        )

    async def get_token_balance(self, token_name: str = 'ETH', check_symbol: bool = True) -> [float, int, str]:
        contract = TOKENS_PER_CHAIN[self.network.name][token_name]
        amount_in_wei = (await self.account.client.call_contract(self.prepare_call(contract, 'balanceOf',
                                                                                   [self.address])))[0]

        decimals = (await self.account.client.call_contract(self.prepare_call(contract, 'decimals')))[0]

        if check_symbol:
            symbol = decode_shortstring((await self.account.client.call_contract(
                self.prepare_call(contract, 'symbol')))[0])

            return amount_in_wei, amount_in_wei / 10 ** decimals, symbol
        return amount_in_wei, amount_in_wei / 10 ** decimals, ''

    def get_approve_call(self, token_address: int, spender_address: int, amount_in_wei: int) -> Call:
        return self.prepare_call(token_address, 'approve', [
            spender_address,
            2 ** 256 - 1 if UNLIMITED_APPROVE else amount_in_wei,
            0
        ])

    async def send_transaction(self, *calls:list, check_hash:bool = False, hash_for_check:int = None):
        try:
            tx_hash = hash_for_check

            if not check_hash:
                tx_hash = (await self.account.execute(
                    calls=calls,
                    auto_estimate=True
                )).transaction_hash

            await self.account.client.wait_for_tx(tx_hash, check_interval=20, retries=1000)

            self.logger.success(f'{self.info} Transaction was successful: {self.explorer}tx/{hex(tx_hash)}')
            return True

        except Exception as error:
            raise RuntimeError(f'Send transaction | {self.get_normalize_error(error)}')

    async def make_request(self, method:str = 'GET', url:str = None, headers:dict = None, params: dict = None,
                           data:str = None, json:dict = None, module_name:str = None):

        async with ClientSession() as session:
            async with session.request(method=method, url=url, headers=headers, data=data,
                                       params=params, json=json, proxy=self.proxy) as response:

                data = await response.json()
                if response.status == 200:
                    return data
                raise RuntimeError(f"Bad request to {module_name} API: {response.status}")

    async def get_gas_price(self):
        url = 'https://alpha-mainnet.starknet.io/feeder_gateway/get_block?blockNumber=latest'

        headers = {
            'Content-Type': 'application/json; charset=utf-8'
        }

        data = (await self.make_request(url=url, headers=headers, module_name='Gas Price'))['gas_price']

        return int(data, 16) / 10 ** 9

    async def get_token_price(self, token_name: str, vs_currency:str = 'usd') -> float:
        token_info = {
            'ETH': 'ethereum',
            'USDT': 'tether',
            'USDC': 'usd-coin',
            'DAI': 'dai'
        }

        if token_name in tuple(token_info.values()):
            token_params = token_name
        elif token_name in tuple(token_info.keys()):
            token_params = token_info[token_name]
        else:
            token_params = token_name

        url = 'https://api.coingecko.com/api/v3/simple/price'

        params = {'ids': f'{token_params}', 'vs_currencies': f'{vs_currency}'}

        data = await self.make_request(url=url, params=params, module_name='CoinGecko')

        return float(data[token_params][vs_currency])




