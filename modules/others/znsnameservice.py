from faker import Faker
from random import randint
from utils.tools import gas_checker, helper
from config import ZNS_CONTRACT, ZNS_ABI
from modules import Minter, Logger


class ZkSyncNameService(Minter, Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)

        self.domain_contract = self.client.get_contract(ZNS_CONTRACT['zns_registrator'], ZNS_ABI)

    async def get_random_name(self):
        domain = f'{Faker().word()}{randint(100, 999999)}'

        check_domain = await self.domain_contract.functions.available(domain).call()

        if check_domain:
            return domain

        await self.get_random_name()

    @helper
    @gas_checker
    async def mint(self):
        self.logger_msg(*self.client.acc_info, msg=f'Mint domain on ZNS')

        domain = await self.get_random_name()

        self.logger_msg(*self.client.acc_info, msg=f'Generated domain: {domain}.zks')

        tx_params = await self.client.prepare_transaction()

        transaction = await self.domain_contract.functions.register(
            domain,
            self.client.address,
            1
        ).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)
