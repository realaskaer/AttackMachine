import asyncio
import random
import aiohttp

from asyncio import sleep
from modules import Logger
from hexbytes import HexBytes
from utils.networks import Network
from config import ERC20_ABI, ZKSYNC_TOKENS
from web3 import AsyncHTTPProvider, AsyncWeb3
from config import RHINO_CHAIN_INFO, ORBITER_CHAINS_INFO, LAYERSWAP_CHAIN_NAME
from settings import (
    GAS_MULTIPLIER,
    UNLIMITED_APPROVE,
    AMOUNT_PERCENT,
    MIN_BALANCE,
    SLIPPAGE_PERCENT,
    DEX_LP_AMOUNT,
    LANDING_AMOUNT,
    OKX_BRIDGE_MODE,
    OKX_DEPOSIT_AMOUNT,
    LAYERSWAP_AMOUNT,
    LAYERSWAP_CHAIN_ID_TO,
    LAYERSWAP_REFUEL,
    ORBITER_AMOUNT,
    ORBITER_CHAIN_ID_TO,
    RHINO_AMOUNT,
    RHINO_CHAIN_ID_TO
)


class Client(Logger):
    def __init__(self, account_number: int, private_key: str, network: Network, proxy: None | str = None):
        super().__init__()
        self.network = network
        self.eip1559_support = network.eip1559_support
        self.token = network.token
        self.explorer = network.explorer
        self.chain_id = network.chain_id

        self.proxy = f"http://{proxy}" if proxy else ""
        self.proxy_init = proxy
        self.request_kwargs = {"proxy": f"http://{proxy}"} if proxy else {}
        self.w3 = AsyncWeb3(AsyncHTTPProvider(random.choice(network.rpc), request_kwargs=self.request_kwargs))
        self.account_number = account_number
        self.private_key = private_key
        self.address = AsyncWeb3.to_checksum_address(self.w3.eth.account.from_key(private_key).address)

        self.min_amount_eth_on_balance = MIN_BALANCE
        self.info = f'[{self.account_number}] {self.address} | Attack Machine |'

    @staticmethod
    def round_amount(min_amount: float, max_amount:float) -> float:
        decimals = max(len(str(min_amount)) - 1, len(str(max_amount)) - 1)
        return round(random.uniform(min_amount, max_amount), decimals)

    @staticmethod
    def get_normalize_error(error):
        if 'message' in error.args[0]:
            error = error.args[0]['message']
        return error

    async def get_normalize_amount(self, token_name, amount_in_wei):
        contract = self.get_contract(ZKSYNC_TOKENS[token_name])
        decimals = await contract.functions.decimals().call()

        return float(amount_in_wei / 10 ** decimals)

    async def get_smart_amount(self, settings):
        if isinstance(settings[0], str):
            _, amount, _ = await self.get_token_balance()

            percent = round(random.uniform(int(settings[0]), int(settings[1]))) / 100
            amount = round(amount * percent, 6)
        else:
            amount = self.round_amount(*settings)
        return amount

    async def price_impact_defender(self, from_token_name, from_token_amount,
                                    to_token_name, to_token_amount_in_wei):

        to_token_amount = await self.get_normalize_amount(to_token_name, to_token_amount_in_wei)

        token_info = {
            'USDT': 'tether',
            'USDC': 'usd-coin',
            'BUSD': 'binance-usd',
            'ETH': 'ethereum',
            'WETH': 'ethereum'
        }

        amount1_in_usd = (await self.get_token_price(token_info[from_token_name])) * from_token_amount
        amount2_in_usd = (await self.get_token_price(token_info[to_token_name])) * to_token_amount
        price_impact = 100 - (amount2_in_usd / amount1_in_usd) * 100

        if price_impact > SLIPPAGE_PERCENT:
            raise RuntimeError(f'Price impact > max slippage | Impact: {price_impact}% > Slippage {SLIPPAGE_PERCENT}%')

    async def bridge_from_source(self, network_to_id) -> None:
        from functions import bridge_layerswap, bridge_rhino, bridge_orbiter

        self.logger.info(f"{self.info} Bridge balance from {self.network.name} for OKX deposit")

        id_of_bridge = {
            1: bridge_rhino,
            2: bridge_orbiter,
            3: bridge_layerswap
        }

        bridge_id = random.choice(OKX_BRIDGE_MODE)

        func = id_of_bridge[bridge_id]

        await asyncio.sleep(1)
        await func(self.account_number, self.private_key, self.network, self.proxy_init,
                   help_okx=True, help_network_id=network_to_id)

    async def get_bridge_data(self, chain_from_id:int, help_okx:bool, help_network_id: int, module_name:str):
        if module_name == 'Rhino':
            source_chain = RHINO_CHAIN_INFO[chain_from_id]
            destination_chain = RHINO_CHAIN_INFO[random.choice(RHINO_CHAIN_ID_TO)]
            amount = await self.get_smart_amount(RHINO_AMOUNT)

            if help_okx:
                source_chain = RHINO_CHAIN_INFO[8]
                destination_chain = RHINO_CHAIN_INFO[help_network_id]
                amount, _ = await self.check_and_get_eth_for_deposit(OKX_DEPOSIT_AMOUNT)

            return source_chain, destination_chain, amount

        elif module_name == 'LayerSwap':
            source_chain = LAYERSWAP_CHAIN_NAME[chain_from_id]
            destination_chain = LAYERSWAP_CHAIN_NAME[random.choice(LAYERSWAP_CHAIN_ID_TO)]
            refuel = LAYERSWAP_REFUEL
            amount = await self.get_smart_amount(LAYERSWAP_AMOUNT)

            if help_okx:
                source_chain = LAYERSWAP_CHAIN_NAME[8]
                destination_chain = LAYERSWAP_CHAIN_NAME[help_network_id]
                amount, _ = await self.check_and_get_eth_for_deposit(OKX_DEPOSIT_AMOUNT)

            return source_chain, destination_chain, amount, refuel

        elif module_name == 'Orbiter':
            source_chain = ORBITER_CHAINS_INFO[chain_from_id]
            destination_chain = ORBITER_CHAINS_INFO[random.choice(ORBITER_CHAIN_ID_TO)]
            amount = await self.get_smart_amount(ORBITER_AMOUNT)

            if help_okx:
                source_chain = ORBITER_CHAINS_INFO[8]
                destination_chain = ORBITER_CHAINS_INFO[help_network_id]
                amount, _ = await self.check_and_get_eth_for_deposit(OKX_DEPOSIT_AMOUNT)

            return source_chain, destination_chain, amount

    async def check_and_get_eth_for_deposit(self, settings:tuple = None) -> [float, int]:
        from functions import swap_odos
        data = await self.get_auto_amount(token_name_search='ETH')

        amount = await self.get_smart_amount(settings if settings else LANDING_AMOUNT)
        amount_in_wei = int(amount * 10 ** 18)

        if data is False:
            self.logger.warning(f'{self.info} Not enough ETH! Launching swap module')

            await asyncio.sleep(1)
            await swap_odos(self.account_number, self.private_key, self.network, self.proxy_init, help_deposit=True)
        else:
            _, _, amount, amount_in_wei = data

        return amount, amount_in_wei

    async def check_and_get_eth_for_liquidity(self) -> [float, int]:
        from functions import swap_oneinch

        eth_balance_in_wei, eth_balance, _ = await self.get_token_balance('ETH')
        amount_from_settings = await self.get_smart_amount(DEX_LP_AMOUNT)
        amount_from_settings_in_wei = int(amount_from_settings * 10 ** 18)

        await asyncio.sleep(1)
        if eth_balance < amount_from_settings:
            self.logger.warning(f'{self.info} Not enough ETH! Launching swap module')
            await asyncio.sleep(1)
            await swap_oneinch(self.account_number, self.private_key, self.network, self.proxy_init,
                               help_add_liquidity=True, amount_to_help=amount_from_settings)

        return amount_from_settings, amount_from_settings_in_wei

    async def get_auto_amount(self, token_name_search:str = None, class_name:str = None) -> [str, float, int]:

        wallet_balance = {k: await self.get_token_balance(k, False) for k, v in ZKSYNC_TOKENS.items()}
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
                                           ZKSYNC_TOKENS.keys()))
            token_names_list.remove('WETH')

            if class_name in ['Maverick', 'Izumi']:
                if 'USDT' in token_names_list:
                    token_names_list.remove('USDT')
                if biggest_token_balance_name == 'ETH' and class_name == 'Izumi':
                    token_names_list.remove('BUSD')
            elif class_name in ['Mute', 'Rango', 'OpenOcean', 'Velocore']:
                if 'BUSD' in token_names_list:
                    token_names_list.remove('BUSD')

            random_to_token_name = random.choice(token_names_list)

            if biggest_token_balance_name == 'ETH':
                percent = round(random.uniform(*AMOUNT_PERCENT)) / 100
            else:
                percent = 1

            amount = round(amount_from_token_on_balance * percent, 7)
            amount_in_wei = round(amount_from_token_on_balance_in_wei * percent)

            return biggest_token_balance_name, random_to_token_name, amount, amount_in_wei

        else:
            raise RuntimeError('Insufficient balance on account!')

    async def get_token_balance(self, token_name: str = 'ETH', check_symbol: bool = True) -> [float, int, str]:
        if token_name != 'ETH':
            contract = self.get_contract(ZKSYNC_TOKENS[token_name])

            amount_in_wei = await contract.functions.balanceOf(self.address).call()
            decimals = await contract.functions.decimals().call()

            if check_symbol:
                symbol = await contract.functions.symbol().call()
                return amount_in_wei, amount_in_wei / 10 ** decimals, symbol
            return amount_in_wei, amount_in_wei / 10 ** decimals, ''

        amount_in_wei = await self.w3.eth.get_balance(self.address)
        return amount_in_wei, amount_in_wei / 10 ** 18, 'ETH'

    def get_contract(self, contract_address: str, abi=ERC20_ABI):
        return self.w3.eth.contract(
            address=AsyncWeb3.to_checksum_address(contract_address),
            abi=abi
        )

    async def get_allowance(self, token_address: str, spender_address: str) -> int:
        contract = self.get_contract(token_address)
        return await contract.functions.allowance(
            self.address,
            spender_address
        ).call()

    async def prepare_transaction(self, value: int = 0):
        try:
            tx_params = {
                'from': self.w3.to_checksum_address(self.address),
                'nonce': await self.w3.eth.get_transaction_count(self.address),
                'value': value,
                'chainId': self.network.chain_id
            }

            if self.network.eip1559_support:

                max_priority_fee_per_gas = 0
                base_fee = await self.w3.eth.gas_price
                max_fee_per_gas = base_fee + max_priority_fee_per_gas

                tx_params['maxPriorityFeePerGas'] = max_priority_fee_per_gas
                tx_params['maxFeePerGas'] = max_fee_per_gas

            else:
                tx_params['gasPrice'] = await self.w3.eth.gas_price

            return tx_params
        except Exception as error:
            raise RuntimeError(f'Prepare transaction | Error: {error}')

    async def make_approve(self, token_address: str, spender_address: str, amount_in_wei: int):
        transaction = await self.get_contract(token_address).functions.approve(
            spender_address,
            amount=2 ** 256 - 1 if UNLIMITED_APPROVE else amount_in_wei
        ).build_transaction(await self.prepare_transaction())

        return await self.send_transaction(transaction)

    async def check_for_approved(self, token_address: str, spender_address: str, amount_in_wei: int) -> bool:
        try:
            contract = self.get_contract(token_address)

            balance_in_wei = await contract.functions.balanceOf(self.address).call()
            symbol = await contract.functions.symbol().call()

            await asyncio.sleep(1)

            self.logger.info(f'{self.info} Check for approval {symbol}')

            await asyncio.sleep(1)

            if balance_in_wei <= 0:
                self.logger.info(f'{self.info} Zero balance')
                return False

            approved_amount_in_wei = await self.get_allowance(
                token_address=token_address,
                spender_address=spender_address
            )
            await asyncio.sleep(1)

            if amount_in_wei <= approved_amount_in_wei:
                self.logger.info(f'{self.info} Already approved')
                return False

            tx_hash = await self.make_approve(
                token_address,
                spender_address,
                amount_in_wei,
            )

            await self.verify_transaction(tx_hash)

            await sleep(random.randint(5, 9))
        except Exception as error:
            raise RuntimeError(f'Check for approve | {self.get_normalize_error(error)}')

    async def send_transaction(self, transaction):
        try:
            transaction['gas'] = int((await self.w3.eth.estimate_gas(transaction)) * GAS_MULTIPLIER)
        except Exception as error:
            raise RuntimeError(f'Gas calculating | {self.get_normalize_error(error)}')

        try:
            singed_tx = self.w3.eth.account.sign_transaction(transaction, self.private_key)

            return await self.w3.eth.send_raw_transaction(singed_tx.rawTransaction)
        except Exception as error:
            raise RuntimeError(f'Send transaction | {self.get_normalize_error(error)}')

    async def verify_transaction(self, tx_hash: HexBytes):
        try:
            data = await self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=360)
            if 'status' in data and data['status'] == 1:
                self.logger.success(f'{self.info} Transaction was successful: {self.explorer}tx/{tx_hash.hex()}')
                return True
            else:
                raise RuntimeError(f'Transaction failed: {self.explorer}tx/{data["transactionHash"].hex()}')
        except Exception as error:
            raise RuntimeError(f'Verify transaction | {self.get_normalize_error(error)}')

    async def get_token_price(self, token_name: str, vs_currency:str = 'usd') -> float:

        url = 'https://api.coingecko.com/api/v3/simple/price'

        params = {'ids': f'{token_name}', 'vs_currencies': f'{vs_currency}'}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, proxy=self.proxy) as response:
                if response.status == 200:
                    data = await response.json()
                    return float(data[token_name][vs_currency])
                raise RuntimeError(f'Bad request to CoinGecko API: {response.status}')
