from faker import Faker
from random import randint
from utils.tools import gas_checker, repeater
from config import ZNS_CONTRACT, ZNS_ABI
from modules import Client


class ZkSyncNameService(Client):
    def __init__(self, account_number, private_key, network, proxy=None):
        super().__init__(account_number, private_key, network, proxy)
        self.domain_contract = self.get_contract(ZNS_CONTRACT['zns_registrator'], ZNS_ABI)

    async def get_random_name(self):
        domain = f'{Faker().word()}{randint(100, 999999)}'

        check_domain = await self.domain_contract.functions.available(domain).call()

        if check_domain:
            return domain

        await self.get_random_name()

    @repeater
    @gas_checker
    async def mint_domain(self):
        self.logger.info(f'{self.info} Mint domain on ZNS')

        domain = await self.get_random_name()

        self.logger.info(f'{self.info} Generated domain: {domain}.zks')

        tx_params = await self.prepare_transaction()

        transaction = await self.domain_contract.functions.register(
            domain,
            self.address,
            1
        ).build_transaction(tx_params)

        tx_hash = await self.send_transaction(transaction)

        await self.verify_transaction(tx_hash)
