import asyncio
import random

from asyncio import sleep
from aiohttp import ClientSession, TCPConnector
from aiohttp_socks import ProxyConnector
from web3.exceptions import TransactionNotFound, TimeExhausted
from modules.interfaces import PriceImpactException, BlockchainException, SoftwareException
from modules import Logger
from utils.networks import Network
from config import ERC20_ABI, TOKENS_PER_CHAIN, ETH_PRICE, CHAIN_IDS, TOKENS_PER_CHAIN2
from web3 import AsyncHTTPProvider, AsyncWeb3
from config import RHINO_CHAIN_INFO, ORBITER_CHAINS_INFO, LAYERSWAP_CHAIN_NAME
from general_settings import (
    GAS_MULTIPLIER,
    UNLIMITED_APPROVE,
    AMOUNT_PERCENT,
    MIN_BALANCE,
    LIQUIDITY_AMOUNT,
    PRICE_IMPACT,
    GLOBAL_NETWORK,
)
from settings import (
    ORBITER_CHAIN_ID_TO,
    ORBITER_DEPOSIT_AMOUNT,
    LAYERSWAP_CHAIN_ID_TO,
    LAYERSWAP_DEPOSIT_AMOUNT,
    RHINO_CHAIN_ID_TO,
    RHINO_DEPOSIT_AMOUNT,
    ACROSS_CHAIN_ID_TO,
    ACROSS_DEPOSIT_AMOUNT, WAIT_FOR_RECEIPT,
)


class Client(Logger):
    def __init__(self, account_name: str | int, private_key: str, network: Network, proxy: None | str = None):
        Logger.__init__(self)
        self.network = network
        self.eip1559_support = network.eip1559_support
        self.token = network.token
        self.explorer = network.explorer
        self.chain_id = network.chain_id

        self.proxy_init = proxy
        self.session = ClientSession(connector=ProxyConnector.from_url(f"http://{proxy}", verify_ssl=False)
                                     if proxy else TCPConnector(verify_ssl=False))
        self.request_kwargs = {"proxy": f"http://{proxy}"} if proxy else {}
        self.rpc = random.choice(network.rpc)
        self.w3 = AsyncWeb3(AsyncHTTPProvider(self.rpc, request_kwargs=self.request_kwargs))
        self.account_name = str(account_name)
        self.private_key = private_key
        self.address = AsyncWeb3.to_checksum_address(self.w3.eth.account.from_key(private_key).address)
        self.acc_info = account_name, self.address

    @staticmethod
    def round_amount(min_amount: float, max_amount: float) -> float:
        decimals = max(len(str(min_amount)) - 1, len(str(max_amount)) - 1)
        return round(random.uniform(min_amount, max_amount), decimals + 2)

    @staticmethod
    def get_normalize_error(error):
        try:
            if isinstance(error.args[0], dict):
                error = error.args[0].get('message', error)
            return error
        except:
            return error

    async def get_decimals(self, token_name: str):
        contract = self.get_contract(TOKENS_PER_CHAIN[self.network.name][token_name])
        return await contract.functions.decimals().call()

    async def get_normalize_amount(self, token_name, amount_in_wei):
        decimals = await self.get_decimals(token_name)
        return float(amount_in_wei / 10 ** decimals)

    async def get_smart_amount(self, settings: tuple = AMOUNT_PERCENT, need_percent: bool = False,
                               token_name: str = 'ETH'):
        if isinstance(settings[0], str) or need_percent:
            _, amount, _ = await self.get_token_balance(token_name)
            percent = round(random.uniform(float(settings[0]), float(settings[1])), 6) / 100
            amount = round(amount * percent, 6)
        else:
            amount = self.round_amount(*settings)
        return amount

    async def price_impact_defender(self, from_token_name, from_token_amount,
                                    to_token_name, to_token_amount_in_wei):

        to_token_amount = await self.get_normalize_amount(to_token_name, to_token_amount_in_wei)

        token_info = {
            'DAI': 'dai',
            'USDT': 'tether',
            'USDC': 'usd-coin',
            'USDC.e': 'bridged-usdc-polygon-pos-bridge',
            'BUSD': 'binance-usd',
            'ETH': 'ethereum',
            'WETH': 'ethereum',
            'USDbC': 'bridged-usd-coin-base'
        }

        amount1_in_usd = (await self.get_token_price(token_info[from_token_name])) * from_token_amount
        amount2_in_usd = (await self.get_token_price(token_info[to_token_name])) * to_token_amount
        price_impact = 100 - (amount2_in_usd / amount1_in_usd) * 100

        if price_impact > PRICE_IMPACT:
            raise PriceImpactException(
                f'DEX price impact > your wanted impact | DEX impact: {price_impact:.3}% > Your impact {PRICE_IMPACT}%')

    async def get_bridge_data(self, chain_from_id: int, module_name: str):
        bridge_info = {
            'Rhino': (RHINO_CHAIN_INFO, RHINO_CHAIN_ID_TO, RHINO_DEPOSIT_AMOUNT),
            'LayerSwap': (LAYERSWAP_CHAIN_NAME, LAYERSWAP_CHAIN_ID_TO, LAYERSWAP_DEPOSIT_AMOUNT),
            'Orbiter': (ORBITER_CHAINS_INFO, ORBITER_CHAIN_ID_TO, ORBITER_DEPOSIT_AMOUNT),
            'Across': (CHAIN_IDS, ACROSS_CHAIN_ID_TO, ACROSS_DEPOSIT_AMOUNT)
        }[module_name]

        deposit_info = bridge_info[2]
        src_chain_id = chain_from_id
        source_chain = bridge_info[0][src_chain_id]
        dst_chains = random.choice(bridge_info[1])
        destination_chain = bridge_info[0][dst_chains]

        amount = await self.get_smart_amount(deposit_info)
        return source_chain, destination_chain, amount, dst_chains

    async def new_client(self, chain_id):
        from functions import get_network_by_chain_id
        from modules import StarknetClient
        if chain_id != 9:
            client = Client
        else:
            client = StarknetClient
        new_client = client(self.account_name, self.private_key,
                            get_network_by_chain_id(chain_id), self.proxy_init)
        return new_client

    async def wait_for_receiving(self, chain_id: int, old_balance: int = 0, token_name: str = 'ETH',
                                 sleep_time: int = 60,
                                 timeout: int = 1200, check_balance_on_dst: bool = False):
        client = await self.new_client(chain_id)

        try:
            if check_balance_on_dst:
                old_balance, _, _ = await client.get_token_balance(token_name)
                return old_balance

            self.logger_msg(*self.acc_info, msg=f'Waiting {token_name} to receive')

            t = 0
            new_eth_balance = 0
            while t < timeout:
                try:
                    new_eth_balance, _, _ = await client.get_token_balance(token_name)
                except:
                    pass

                if new_eth_balance > old_balance:
                    dicimals = await client.get_decimals(token_name) if token_name != client.network.token else 18
                    amount = round((new_eth_balance - old_balance) / 10 ** dicimals, 6)
                    self.logger_msg(*self.acc_info, msg=f'{amount} {token_name} was received', type_msg='success')
                    return True
                else:
                    self.logger_msg(*self.acc_info, msg=f'Still waiting {token_name} to receive...', type_msg='warning')
                    await asyncio.sleep(sleep_time)
                    t += sleep_time
                if t > timeout:
                    raise RuntimeError(f'{token_name} has not been received within {timeout} seconds')
        except Exception as error:
            raise SoftwareException(f'Error in <WAIT FOR RECEIVING> function. Error: {error}')
        finally:
            await client.session.close()

    async def get_token_balance(self, token_name: str = 'ETH', check_symbol: bool = True,
                                omnicheck: bool = False, check_native: bool = False) -> [float, int, str]:
        if not check_native:
            if token_name != self.network.token:
                if omnicheck:
                    contract = self.get_contract(TOKENS_PER_CHAIN2[self.network.name][token_name])
                else:
                    contract = self.get_contract(TOKENS_PER_CHAIN[self.network.name][token_name])

                amount_in_wei = await contract.functions.balanceOf(self.address).call()
                decimals = await contract.functions.decimals().call()

                if check_symbol:
                    symbol = await contract.functions.symbol().call()
                    return amount_in_wei, amount_in_wei / 10 ** decimals, symbol
                return amount_in_wei, amount_in_wei / 10 ** decimals, ''

        amount_in_wei = await self.w3.eth.get_balance(self.address)
        return amount_in_wei, amount_in_wei / 10 ** 18, self.network.token

    async def check_and_get_eth(self, settings: tuple = None, bridge_mode: bool = False,
                                initial_chain_id: int = 0) -> [float, int]:
        from functions import swap_odos, swap_oneinch, swap_openocean, swap_xyfinance, swap_rango

        try:
            func = {
                3: [swap_odos, swap_oneinch, swap_openocean, swap_xyfinance],
                4: [swap_rango, swap_openocean, swap_xyfinance],
                6: [swap_oneinch],
                8: [swap_openocean, swap_xyfinance],
                11: [swap_openocean, swap_xyfinance, swap_rango, swap_odos, swap_oneinch]
            }[GLOBAL_NETWORK]

            module_func = random.choice(func)

            data = True
            if bridge_mode and initial_chain_id in [2, 3, 4, 8, 9, 11, 12]:
                data = await self.get_auto_amount(token_name_search='ETH')
            elif not bridge_mode:
                data = await self.get_auto_amount(token_name_search='ETH')

            if data is False:
                self.logger_msg(*self.acc_info, msg=f'Not enough ETH! Launching swap module', type_msg='warning')
                await module_func(self.account_name, self.private_key, self.network, self.proxy_init, help_deposit=True)
        except:
            pass

        amount = await self.get_smart_amount(settings if settings else LIQUIDITY_AMOUNT)
        amount_in_wei = int(amount * 10 ** 18)

        return amount, amount_in_wei

    async def get_auto_amount(self, token_name_search: str = None, class_name: str = None) -> [str, float, int]:

        wallet_balance = {k: await self.get_token_balance(k, False)
                          for k, v in TOKENS_PER_CHAIN[self.network.name].items()}
        valid_wallet_balance = {k: v[1] for k, v in wallet_balance.items() if v[0] != 0}
        eth_price = ETH_PRICE

        if 'ETH' in valid_wallet_balance:
            valid_wallet_balance['ETH'] = valid_wallet_balance['ETH'] * eth_price

        if 'WETH' in valid_wallet_balance:
            valid_wallet_balance['WETH'] = valid_wallet_balance['WETH'] * eth_price

        if sum(valid_wallet_balance.values()) > MIN_BALANCE * eth_price:

            valid_wallet_balance = {k: round(v, 7) for k, v in valid_wallet_balance.items()}

            biggest_token_balance_name = max(valid_wallet_balance, key=lambda x: valid_wallet_balance[x])

            if token_name_search == 'ETH' and biggest_token_balance_name != 'ETH':
                return False
            elif token_name_search == 'ETH' and biggest_token_balance_name == 'ETH':
                return True

            amount_from_token_on_balance = wallet_balance[biggest_token_balance_name][1]
            amount_from_token_on_balance_in_wei = wallet_balance[biggest_token_balance_name][0]

            token_names_list = list(filter(lambda token_name: token_name != biggest_token_balance_name,
                                           TOKENS_PER_CHAIN[self.network.name].keys()))

            if biggest_token_balance_name != 'WETH':
                token_names_list.remove('WETH')

            if biggest_token_balance_name == 'ETH':
                if GLOBAL_NETWORK == 11:
                    if class_name in ['Maverick', 'Izumi']:
                        if 'USDT' in token_names_list:
                            token_names_list.remove('USDT')
                        if biggest_token_balance_name == 'ETH' and class_name == 'Izumi':
                            token_names_list.remove('BUSD')
                    elif class_name in ['Mute', 'Rango', 'OpenOcean', 'Velocore']:
                        if 'BUSD' in token_names_list:
                            token_names_list.remove('BUSD')
                elif GLOBAL_NETWORK == 4:
                    if class_name in ['WooFi']:
                        if 'USDT' in token_names_list:
                            token_names_list.remove('USDT')
            else:
                token_names_list = ['ETH']

            random_to_token_name = random.choice(token_names_list)
            if not random_to_token_name:
                raise RuntimeError(f'No available pair from {biggest_token_balance_name}')

            if biggest_token_balance_name == 'ETH':
                percent = round(random.uniform(*AMOUNT_PERCENT), 9) / 100
            else:
                percent = 1

            amount = round(amount_from_token_on_balance * percent, 7)
            amount_in_wei = int(amount_from_token_on_balance_in_wei * percent)

            return biggest_token_balance_name, random_to_token_name, amount, amount_in_wei

        else:
            raise SoftwareException('Insufficient balance on account!')

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

    async def get_priotiry_fee(self):
        fee_history = await self.w3.eth.fee_history(25, 'latest', [20.0])
        non_empty_block_priority_fees = [fee[0] for fee in fee_history["reward"] if fee[0] != 0]

        divisor_priority = max(len(non_empty_block_priority_fees), 1)

        priority_fee = int(round(sum(non_empty_block_priority_fees) / divisor_priority))

        return priority_fee

    async def prepare_transaction(self, value: int = 0):
        try:
            tx_params = {
                'from': self.w3.to_checksum_address(self.address),
                'nonce': await self.w3.eth.get_transaction_count(self.address),
                'value': value,
                'chainId': self.network.chain_id
            }

            if self.network.eip1559_support:

                base_fee = await self.w3.eth.gas_price
                max_priority_fee_per_gas = await self.get_priotiry_fee()
                max_fee_per_gas = base_fee + max_priority_fee_per_gas

                tx_params['maxPriorityFeePerGas'] = max_priority_fee_per_gas
                tx_params['maxFeePerGas'] = max_fee_per_gas
                tx_params['type'] = '0x2'
            else:
                if self.network.name == 'BNB Chain':
                    tx_params['gasPrice'] = self.w3.to_wei(round(random.uniform(1.2, 1.5), 1), 'gwei')
                else:
                    tx_params['gasPrice'] = await self.w3.eth.gas_price

            return tx_params
        except Exception as error:
            raise BlockchainException(f'Prepare transaction | Error: {self.get_normalize_error(error)}')

    async def make_approve(self, token_address: str, spender_address: str, amount_in_wei: int):
        transaction = await self.get_contract(token_address).functions.approve(
            spender_address,
            amount=2 ** 256 - 1 if UNLIMITED_APPROVE else amount_in_wei
        ).build_transaction(await self.prepare_transaction())

        return await self.send_transaction(transaction)

    async def check_for_approved(self, token_address: str, spender_address: str,
                                 amount_in_wei: int, without_bal_check: bool = False) -> bool:
        try:
            contract = self.get_contract(token_address)

            balance_in_wei = await contract.functions.balanceOf(self.address).call()
            symbol = await contract.functions.symbol().call()

            await asyncio.sleep(1)

            self.logger_msg(*self.acc_info, msg=f'Check for approval {symbol}')

            await asyncio.sleep(1)

            if not without_bal_check and balance_in_wei <= 0:
                raise RuntimeError(f'Zero {symbol} balance')

            approved_amount_in_wei = await self.get_allowance(
                token_address=token_address,
                spender_address=spender_address
            )
            await asyncio.sleep(1)

            if amount_in_wei <= approved_amount_in_wei:
                self.logger_msg(*self.acc_info, msg=f'Already approved')
                return False

            result = await self.make_approve(token_address, spender_address, amount_in_wei)

            await sleep(random.randint(5, 9))
            return result
        except Exception as error:
            raise BlockchainException(f'Check for approve | {self.get_normalize_error(error)}')

    async def send_transaction(self, transaction, need_hash: bool = False, without_gas: bool = False,
                               poll_latency: int = 10, timeout: int = 360):
        try:
            if not without_gas:
                transaction['gas'] = int((await self.w3.eth.estimate_gas(transaction)) * GAS_MULTIPLIER)
        except Exception as error:
            raise BlockchainException(f'Gas calculating | {self.get_normalize_error(error)}')

        try:
            singed_tx = self.w3.eth.account.sign_transaction(transaction, self.private_key)
            tx_hash = await self.w3.eth.send_raw_transaction(singed_tx.rawTransaction)
        except Exception as error:
            if self.get_normalize_error(error) == 'already known':
                self.logger_msg(*self.acc_info, msg='RPC got error, but tx was send', type_msg='warning')
                return True
            else:
                raise BlockchainException(f'Send transaction | {self.get_normalize_error(error)}')

        try:

            total_time = 0
            timeout = timeout if self.network.name != 'Polygon' else 1200
            while True:
                try:
                    receipts = await self.w3.eth.get_transaction_receipt(tx_hash)
                    status = receipts.get("status")
                    if status == 1:
                        message = f'Transaction was successful: {self.explorer}tx/{tx_hash.hex()}'
                        self.logger_msg(*self.acc_info, msg=message, type_msg='success')
                        if need_hash:
                            return tx_hash
                        return True
                    elif status is None:
                        await asyncio.sleep(poll_latency)
                    else:
                        self.logger_msg(*self.acc_info, msg=f'Transaction failed: {self.explorer}tx/{tx_hash.hex()}',
                                        type_msg='error')
                        return False
                except TransactionNotFound:
                    if total_time > timeout:
                        raise TimeExhausted(f"Transaction {tx_hash !r} is not in the chain after {timeout} seconds")
                    total_time += poll_latency
                    await asyncio.sleep(poll_latency)

                except Exception as error:
                    self.logger_msg(*self.acc_info, msg=f'RPC got autims response. Error: {error}', type_msg='warning')
                    total_time += poll_latency
                    await asyncio.sleep(poll_latency)
        except Exception as error:
            raise BlockchainException(f'Verify transaction | {self.get_normalize_error(error)}')

    async def get_token_price(self, token_name: str, vs_currency: str = 'usd') -> float:

        url = 'https://api.coingecko.com/api/v3/simple/price'

        params = {'ids': f'{token_name}', 'vs_currencies': f'{vs_currency}'}

        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return float(data[token_name][vs_currency])
            raise SoftwareException(f'Bad request to CoinGecko API: {response.status}')

    async def wait_for_l0_received(self, tx_hash):
        if not WAIT_FOR_RECEIPT:
            return True

        url = f"https://api-mainnet.layerzero-scan.com/tx/{tx_hash.hex()}"

        t = 0
        sleep_time = 20
        timeout = 600 if self.network.name != 'Polygon' else 3600
        flag = False
        while t < timeout:
            try:
                async with self.session.get(url=url) as response:
                    result = await response.json()

                    if (len(result["messages"]) > 0 and "dstTxHash" in result["messages"][0]
                            and "status" in result["messages"][0] and result["messages"][0]["status"] == "DELIVERED"):
                        flag = True
            except:
                pass

            if flag:
                self.logger_msg(*self.acc_info, msg=f'Funds were received on destination chain', type_msg='success')
                return True
            else:
                self.logger_msg(
                    *self.acc_info, msg=f'Waiting for funds on destination chain...', type_msg='warning')
                await asyncio.sleep(sleep_time)
                t += sleep_time
            if t > timeout:
                raise SoftwareException(f'Funds have not been received on destination chain within {timeout} seconds')

        async with self.session.get(url=url) as response:
            result = await response.json()

            if (len(result["messages"]) > 0 and "dstTxHash" in result["messages"][0]
                    and 'status' in result["messages"][0] and result["messages"][0]['status'] == "DELIVERED"):
                return True
