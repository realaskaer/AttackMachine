from aiohttp import ContentTypeError, ClientSession
from loguru import logger
from sys import stderr
from datetime import datetime
from web3 import AsyncWeb3
from abc import ABC, abstractmethod
from random import uniform

from settings import (LAYERSWAP_API_KEY, OKX_API_KEY, OKX_API_PASSPHRAS,
                      OKX_API_SECRET, GLOBAL_NETWORK)
from utils.networks import StarknetRPC

CHAINS_NAME = {
    2: 'Arbitrum Nova',
    3: 'Base',
    4: 'Linea',
    8: 'Scroll',
    9: 'Starknet',
    11: 'zkSync',
    12: 'Zora'
}

random_version = f"{uniform(520, 540):.2f}"
USER_AGENT = (f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/{random_version} (KHTML, like Gecko)'
              f' Chrome/119.0.0.0 Safari/{random_version} Edg/119.0.0.0')


class Logger(ABC):
    def __init__(self):
        self.logger = logger
        self.logger.remove()
        logger_format = "<cyan>{time:HH:mm:ss}</cyan> | <level>" "{level: <8}</level> | <level>{message}</level>"
        self.logger.add(stderr, format=logger_format)
        date = datetime.today().date()
        self.logger.add(f"./data/logs/{date}.log", rotation="500 MB", level="INFO", format=logger_format)

    def logger_msg(self, account_name, address, msg, type_msg: str = 'info'):
        if account_name is None and address is None:
            info = f'[Attack machine] | {CHAINS_NAME[GLOBAL_NETWORK]} | {self.__class__.__name__} |'
        elif account_name is not None and address is None:
            info = f'[{account_name}] | {CHAINS_NAME[GLOBAL_NETWORK]} | {self.__class__.__name__} |'
        else:
            address = hex(address) if GLOBAL_NETWORK == 9 else address
            info = f'[{account_name}] | {address} | {CHAINS_NAME[GLOBAL_NETWORK]} | {self.__class__.__name__} |'
        if type_msg == 'info':
            self.logger.info(f"{info} {msg}")
        elif type_msg == 'error':
            self.logger.error(f"{info} {msg}")
        elif type_msg == 'success':
            self.logger.success(f"{info} {msg}")
        elif type_msg == 'warning':
            self.logger.warning(f"{info} {msg}")


class DEX(ABC):
    @abstractmethod
    async def swap(self):
        pass


class CEX(ABC):
    def __init__(self, client):
        self.client = client

        self.api_key = OKX_API_KEY
        self.api_secret = OKX_API_SECRET
        self.passphras = OKX_API_PASSPHRAS

    @abstractmethod
    async def deposit(self):
        pass

    @abstractmethod
    async def withdraw(self):
        pass

    @staticmethod
    async def make_request(method:str = 'GET', url:str = None, data:str = None, params:dict = None,
                           headers:dict = None, json:dict = None, module_name:str = 'Request'):

        async with ClientSession() as session:
            async with session.request(method=method, url=url, headers=headers, data=data, json=json,
                                       params=params) as response:

                data = await response.json()
                if data['code'] != 0 and data['msg'] != '':
                    error = f"Error code: {data['code']} Msg: {data['msg']}"
                    raise RuntimeError(f"Bad request to OKX({module_name}): {error}")
                else:
                    # self.logger.success(f"{self.info} {module_name}")
                    return data['data']


class Aggregator(ABC):
    def __init__(self, client):
        self.client = client

    @abstractmethod
    async def swap(self):
        pass

    async def make_request(self, method:str = 'GET', url:str = None, headers:dict = None, params: dict = None,
                           data:str = None, json:dict = None):

        headers = (headers or {}) | {'User-Agent': USER_AGENT}
        async with self.client.session.request(method=method, url=url, headers=headers, data=data,
                                               params=params, json=json) as response:
            try:
                data = await response.json()
                if response.status == 200:
                    return data
                raise RuntimeError(f"Bad request to {self.__class__.__name__} API: {response.status}")
            except ContentTypeError:
                raise RuntimeError(f"Bad request to {self.__class__.__name__} API. Problem in API functionality")


class Bridge(ABC):
    def __init__(self, client):
        self.client = client

        if self.__class__.__name__ == 'LayerSwap':
            self.headers = {
                'X-LS-APIKEY': f'{LAYERSWAP_API_KEY}',
                'Content-Type': 'application/json'
            }
        elif self.__class__.__name__ == 'Rhino':
            self.headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
            }

    async def get_address_for_bridge(self, private_key:str, stark_key_type:bool):
        from modules import StarknetClient
        if private_key is None:
            return
        elif stark_key_type:
            stark_client = None
            try:
                stark_client = StarknetClient('Bridge', private_key, StarknetRPC, self.client.proxy_init)
                await stark_client.initialize_account()
                return hex(stark_client.address)
            finally:
                await stark_client.session.close()
        else:
            return AsyncWeb3().eth.account.from_key(private_key).address

    @abstractmethod
    async def bridge(self, *args, **kwargs):
        pass

    async def make_request(self, method:str = 'GET', url:str = None, headers:dict = None, params: dict = None,
                           data:str = None, json:dict = None):

        headers = (headers or {}) | {'User-Agent': USER_AGENT}
        async with self.client.session.request(method=method, url=url, headers=headers, data=data,
                                               params=params, json=json) as response:

            data = await response.json()
            if response.status in [200, 201]:
                return data
            raise RuntimeError(f"Bad request to {self.__class__.__name__} API: {response.status}")


class Refuel(ABC):
    @abstractmethod
    async def refuel(self):
        pass


class Messenger(ABC):
    @abstractmethod
    async def send_message(self):
        pass


class Landing(ABC):
    @abstractmethod
    async def deposit(self):
        pass

    @abstractmethod
    async def withdraw(self):
        pass

    @abstractmethod
    async def enable_collateral(self):
        pass

    @abstractmethod
    async def disable_collateral(self):
        pass


class Minter(ABC):
    @abstractmethod
    async def mint(self):
        pass


class Creator(ABC):
    @abstractmethod
    async def create(self):
        pass


class Blockchain(ABC):
    def __init__(self, client):
        self.client = client

    @abstractmethod
    async def deposit(self):
        pass

    @abstractmethod
    async def withdraw(self):
        pass

    async def make_request(self, method:str = 'GET', url:str = None, headers:dict = None, params: dict = None,
                           data:str = None, json:dict = None):

        headers = (headers or {}) | {'User-Agent': USER_AGENT}
        async with self.client.session.request(method=method, url=url, headers=headers, data=data,
                                               params=params, json=json) as response:

            data = await response.json()
            if response.status == 200:
                return data
            raise RuntimeError(f"Bad request to {self.__class__.__name__} API: {response.status}")
