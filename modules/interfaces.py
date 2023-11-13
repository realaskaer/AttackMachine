from aiohttp import ClientSession
from loguru import logger
from sys import stderr
from web3 import AsyncWeb3
from abc import ABC, abstractmethod
from settings import LAYERSWAP_API_KEY, OKX_API_KEY, OKX_API_PASSPHRAS, OKX_API_SECRET, OKX_DEPOSIT_NETWORK


class DEX(ABC):
    @abstractmethod
    async def swap(self):
        pass


class Logger(ABC):
    def __init__(self):
        self.logger = logger
        self.logger.remove()
        logger_format = "<cyan>{time:HH:mm:ss}</cyan> | <level>" "{level: <8}</level> | <level>{message}</level>"
        self.logger.add(stderr, format=logger_format)
        self.logger.add("./data/logs/logfile.log", rotation="500 MB", level="INFO", format=logger_format)

    def logger_msg(self, account_name, private_key, msg, type_msg: str = 'info'):
        if account_name is None or private_key is None:
            info = f'[Attack machine] | Runner |'
        else:
            address = AsyncWeb3().eth.account.from_key(private_key).address
            info = f'[{account_name}] {address} | Runner |'
        if type_msg == 'info':
            self.logger.info(f"{info} {msg}")
        elif type_msg == 'error':
            self.logger.error(f"{info} {msg}")
        elif type_msg == 'success':
            self.logger.success(f"{info} {msg}")
        elif type_msg == 'warning':
            self.logger.warning(f"{info} {msg}")


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

    async def make_request(self, method:str = 'GET', url:str = None, data:str = None, params:dict = None,
                           headers:dict = None, module_name:str = 'Request'):

        async with ClientSession() as session:
            async with session.request(method=method, url=url, headers=headers, data=data,
                                       params=params, proxy=self.client.proxy) as response:

                data = await response.json()
                if data['code'] != 0 and data['msg'] != '':
                    error = f"Error code: {data['code']} Msg: {data['msg']}"
                    raise RuntimeError(f"Bad request to OKX({module_name}): {error}")
                else:
                    #self.logger.success(f"{self.info} {module_name}")
                    return data['data']


class Aggregator(ABC):
    def __init__(self, client):
        self.client = client

    @abstractmethod
    async def swap(self):
        pass

    async def make_request(self, method:str = 'GET', url:str = None, headers:dict = None, params: dict = None,
                           data:str = None, json:dict = None):

        async with ClientSession() as session:
            async with session.request(method=method, url=url, headers=headers, data=data,
                                       params=params, json=json, proxy=self.client.proxy) as response:

                data = await response.json()
                if response.status == 200:
                    return data
                raise RuntimeError(f"Bad request to {self.__class__.__name__} API: {response.status}")


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

    @abstractmethod
    async def bridge(self, *args, **kwargs):
        pass

    async def make_request(self, method:str = 'GET', url:str = None, headers:dict = None, params: dict = None,
                           data:str = None, json:dict = None):

        async with ClientSession() as session:
            async with session.request(method=method, url=url, headers=headers, data=data,
                                       params=params, json=json, proxy=self.client.proxy) as response:

                data = await response.json()
                if response.status == 200:
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
    def __init__(self, client):
        self.client = client

    @abstractmethod
    async def create(self):
        pass


class Blockchain(ABC):
    @abstractmethod
    async def deposit(self):
        pass

    @abstractmethod
    async def withdraw(self):
        pass

    @abstractmethod
    async def transfer_eth(self):
        pass

    @abstractmethod
    async def wrap_eth(self):
        pass

    @abstractmethod
    async def unwrap_eth(self):
        pass
