from faker import Faker
from random import randint
from utils.tools import gas_checker, repeater
from config import ZNS_CONTRACT, ZNS_ABI
from modules import Minter


class ZkSyncNameService(Minter):
    def __init__(self, client):
        self.client = client

        self.domain_contract = self.client.get_contract(ZNS_CONTRACT['zns_registrator'], ZNS_ABI)

    async def get_random_name(self):
        domain = f'{Faker().word()}{randint(100, 999999)}'

        check_domain = await self.domain_contract.functions.available(domain).call()

        if check_domain:
            return domain

        await self.get_random_name()

    @repeater
    @gas_checker
    async def mint(self):
        self.client.logger.info(f'{self.client.info} Mint domain on ZNS')

        domain = await self.get_random_name()

        self.client.logger.info(f'{self.client.info} Generated domain: {domain}.zks')

        tx_params = await self.client.prepare_transaction()

        transaction = await self.domain_contract.functions.register(
            domain,
            self.client.address,
            1
        ).build_transaction(tx_params)

        tx_hash = await self.client.send_transaction(transaction)

        return await self.client.verify_transaction(tx_hash)
