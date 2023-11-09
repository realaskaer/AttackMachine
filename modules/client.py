import asyncio
import random
import aiohttp

from sys import stderr
from loguru import logger
from asyncio import sleep
from hexbytes import HexBytes
from utils.networks import Network
from config import ERC20_ABI, ZKSYNC_TOKENS
from web3 import AsyncHTTPProvider, AsyncWeb3
from config import RHINO_CHAIN_INFO, ORBITER_CHAINS_INFO, LAYERSWAP_CHAIN_NAME
from settings import (
    GAS_MULTIPLIER,
    UNLIMITED_APPROVE,
    AMOUNT_MIN,
    AMOUNT_MAX,
    MIN_BALANCE,
    DEX_LP_MAX,
    DEX_LP_MIN,
    OKX_BRIDGE_MODE,
    OKX_DEPOSIT_AMOUNT,
    LAYERSWAP_AMOUNT_MIN,
    LAYERSWAP_AMOUNT_MAX,
    LAYERSWAP_CHAIN_ID_TO,
    LAYERSWAP_REFUEL,
    ORBITER_AMOUNT_MIN,
    ORBITER_AMOUNT_MAX,
    ORBITER_CHAIN_ID_TO,
    RHINO_AMOUNT_MAX,
    RHINO_AMOUNT_MIN,
    RHINO_CHAIN_ID_TO
)


class Client:
    def __init__(self, account_number: int, private_key: str, network: Network, proxy: None | str = None):
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
        self.logger = logger
        self.info = f'[{self.account_number}] {self.address[:10]}....{self.address[-6:]} |'
        self.logger.remove()
        logger_format = "<cyan>{time:HH:mm:ss}</cyan> | <level>" "{level: <8}</level> | <level>{message}</level>"
        self.logger.add(stderr, format=logger_format)

    @staticmethod
    def round_amount(min_amount: float, max_amount:float) -> float:
        decimals = max(len(str(min_amount)) - 1, len(str(max_amount)) - 1)
        return round(random.uniform(min_amount, max_amount), decimals)

    async def bridge_from_source(self, network_to_id) -> None:
        from functions import bridge_layerswap, bridge_rhino, bridge_orbiter

        self.logger.info(f"{self.info} {self.__class__.__name__} | Bridge balance from {self.network.name}")

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
            chain_from_name = RHINO_CHAIN_INFO[chain_from_id]
            chain_to_name = RHINO_CHAIN_INFO[random.choice(RHINO_CHAIN_ID_TO)]

            if isinstance(RHINO_AMOUNT_MIN, str):
                _, amount, _ = await self.get_token_balance()

                percent = round(random.uniform(int(RHINO_AMOUNT_MIN), int(RHINO_AMOUNT_MAX))) / 100
                amount = round(amount * percent, 6)
            else:
                amount = self.round_amount(RHINO_AMOUNT_MIN, RHINO_AMOUNT_MAX)

            if help_okx:
                chain_from_name = RHINO_CHAIN_INFO[8]
                chain_to_name = RHINO_CHAIN_INFO[help_network_id]
                amount, _ = await self.check_and_get_eth_for_deposit(OKX_DEPOSIT_AMOUNT)

            return chain_from_name, chain_to_name, amount

        elif module_name == 'LayerSwap':
            source_chain = LAYERSWAP_CHAIN_NAME[chain_from_id]
            destination_chain = LAYERSWAP_CHAIN_NAME[random.choice(LAYERSWAP_CHAIN_ID_TO)]
            source_asset, destination_asset = 'ETH', 'ETH'
            refuel = LAYERSWAP_REFUEL

            if isinstance(LAYERSWAP_AMOUNT_MIN, str):
                _, amount, _ = await self.get_token_balance()
                percent = round(random.uniform(int(LAYERSWAP_AMOUNT_MIN), int(LAYERSWAP_AMOUNT_MAX))) / 100
                amount = round(amount * percent, 6)
            else:
                amount = self.round_amount(LAYERSWAP_AMOUNT_MIN, LAYERSWAP_AMOUNT_MAX)

            if help_okx:
                source_chain = LAYERSWAP_CHAIN_NAME[8]
                destination_chain = LAYERSWAP_CHAIN_NAME[help_network_id]
                amount, _ = await self.check_and_get_eth_for_deposit(OKX_DEPOSIT_AMOUNT)

            return source_chain, destination_chain, source_asset, destination_asset, amount, refuel

        elif module_name == 'Orbiter':
            from_chain = ORBITER_CHAINS_INFO[chain_from_id]
            to_chain = ORBITER_CHAINS_INFO[random.choice(ORBITER_CHAIN_ID_TO)]
            token_name = 'ETH'

            if isinstance(ORBITER_AMOUNT_MIN, str):
                _, amount, _ = await self.get_token_balance()
                percent = round(random.uniform(int(ORBITER_AMOUNT_MIN), int(ORBITER_AMOUNT_MAX))) / 100
                amount = round(amount * percent, 6)
            else:
                amount = self.round_amount(ORBITER_AMOUNT_MIN, ORBITER_AMOUNT_MAX)

            if help_okx:
                from_chain = ORBITER_CHAINS_INFO[8]
                to_chain = ORBITER_CHAINS_INFO[help_network_id]
                amount, _ = await self.check_and_get_eth_for_deposit(OKX_DEPOSIT_AMOUNT)

            return from_chain, to_chain, token_name, amount

    async def check_and_get_eth_for_deposit(self, okx_percent: int = 0) -> [float, int]:
        from functions import swap_odos
        data = await self.get_auto_amount(token_name_search='ETH')

        if data is False:
            self.logger.warning(f'{self.info} {self.__class__.__name__} | Not enough ETH! Launching swap module')

            await asyncio.sleep(1)
            await swap_odos(self.account_number, self.private_key, self.network, self.proxy_init, help_deposit=True)

            percent = round(random.uniform(AMOUNT_MIN, AMOUNT_MAX)) / 100
            balance_in_wei, balance, _ = await self.get_token_balance()
            if okx_percent:
                percent = okx_percent
            amount = round(balance * percent, 7)
            amount_in_wei = int(balance_in_wei * percent)
        else:
            _, _, amount, amount_in_wei = data

        return amount, amount_in_wei

    async def check_and_get_eth_for_liquidity(self) -> [float, int]:
        from functions import swap_oneinch
        class_name = self.__class__.__name__

        eth_balance_in_wei, eth_balance, _ = await self.get_token_balance('ETH')
        amount_from_settings = self.round_amount(DEX_LP_MIN, DEX_LP_MAX)
        amount_from_settings_in_wei = int(amount_from_settings * 10 ** 18)

        await asyncio.sleep(1)
        if eth_balance < amount_from_settings:
            self.logger.warning(f'{self.info} {class_name} | Not enough ETH to add liquidity! Launching swap module')
            await asyncio.sleep(1)
            await swap_oneinch(self.account_number, self.private_key, self.network, self.proxy_init,
                               help_add_liquidity=True, amount_to_help=amount_from_settings)

        return amount_from_settings, amount_from_settings_in_wei

    async def get_auto_amount(self, token_name_search:str = None) -> [str, float, int]:

        wallet_balance = {k: await self.get_token_balance(k, False) for k, v in ZKSYNC_TOKENS.items()}
        valid_wallet_balance = {k: v[1] for k, v in wallet_balance.items() if v[0] != 0}
        eth_price = await self.get_token_price('ethereum')

        if 'ETH' in valid_wallet_balance:
            valid_wallet_balance['ETH'] = valid_wallet_balance['ETH'] * eth_price

        if sum(valid_wallet_balance.values()) > self.min_amount_eth_on_balance * eth_price:

            valid_wallet_balance = {k: round(v, 7) for k, v in valid_wallet_balance.items()}

            from_token_name = max(valid_wallet_balance, key=lambda x: valid_wallet_balance[x])

            if token_name_search == 'ETH' and from_token_name != 'ETH':
                return False

            amount_from_token_on_balance_in_wei = wallet_balance[from_token_name][0]
            amount_from_token_on_balance = wallet_balance[from_token_name][1]

            token_names_list = list(filter(lambda token_name: token_name != from_token_name, ZKSYNC_TOKENS.keys()))
            token_names_list.remove('WETH')

            # if self.__class__.__name__ in ['OpenOcean']:
            #     if 'BUSD' in token_names_list:
            #         token_names_list.remove('BUSD')

            to_token_name = random.choice(token_names_list)

            if from_token_name == 'ETH':
                percent = round(random.uniform(AMOUNT_MIN, AMOUNT_MAX)) / 100
            else:
                percent = 1

            amount = round(amount_from_token_on_balance * percent, 7)
            amount_in_wei = round(amount_from_token_on_balance_in_wei * percent)

            return from_token_name, to_token_name, amount, amount_in_wei

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
            class_name = self.__class__.__name__
            contract = self.get_contract(token_address)

            balance_in_wei = await contract.functions.balanceOf(self.address).call()
            symbol = await contract.functions.symbol().call()

            await asyncio.sleep(1)

            self.logger.info(f'{self.info} {class_name} Check approval {symbol} for spending by {class_name}')

            await asyncio.sleep(1)

            if balance_in_wei <= 0:
                self.logger.info(f'{self.info} {class_name} | Zero balance')
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
            raise RuntimeError(f'Check for approve | {error}')

    async def send_transaction(self, transaction):
        try:
            transaction['gas'] = int((await self.w3.eth.estimate_gas(transaction)) * GAS_MULTIPLIER)
        except Exception as error:
            if 'message' in error.args[0]:
                error = error.args[0]['message']
            raise RuntimeError(f'Gas calculating | {error}')

        try:
            singed_tx = self.w3.eth.account.sign_transaction(transaction, self.private_key)

            return await self.w3.eth.send_raw_transaction(singed_tx.rawTransaction)
        except Exception as error:
            raise RuntimeError(f'Send transaction | {error.args[0]["message"]}')

    async def verify_transaction(self, tx_hash: HexBytes):
        try:
            data = await self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=360)
            if 'status' in data and data['status'] == 1:
                self.logger.success(f'{self.info} {self.__class__.__name__} |'
                                    f' Transaction was successful: {self.explorer}tx/{tx_hash.hex()}')
            else:
                raise RuntimeError(f'Transaction failed: {self.explorer}tx/{data["transactionHash"].hex()}')
        except Exception as error:
            raise RuntimeError(f'Verify transaction | {error}')

    async def get_token_price(self, token_name: str, vs_currency:str = 'usd') -> float:

        url = 'https://api.coingecko.com/api/v3/simple/price'

        params = {'ids': f'{token_name}', 'vs_currencies': f'{vs_currency}'}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, proxy=self.proxy) as response:
                if response.status == 200:
                    data = await response.json()
                    return float(data[token_name][vs_currency])
                raise RuntimeError(f'Bad request to CoinGecko API: {response.status}')
