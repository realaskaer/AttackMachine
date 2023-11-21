from random import randint
from faker import Faker
from utils.tools import gas_checker, repeater
from modules import Minter
from config import ENS_ABI, ENS_CONTRACT


class EraDomainService(Minter):
    def __init__(self, client):
        self.client = client

        self.domain_contract = self.client.get_contract(ENS_CONTRACT['era_name_service'], ENS_ABI)

    async def get_random_name(self):
        domain = f'{Faker().word()}{randint(100, 999999)}'

        check_domain = await self.domain_contract.functions._checkName(domain).call()

        if check_domain:
            return domain

        await self.get_random_name()

    @repeater
    @gas_checker
    async def mint(self):

        _, _ = await self.client.check_and_get_eth_for_deposit()

        self.client.logger.info(f'{self.client.info} Mint domain on ENS: 0.003 ETH')

        price_in_wei = 3000000000000000

        domain = await self.get_random_name()

        self.client.logger.info(f'{self.client.info} Generated domain: {domain}.era')

        tx_params = await self.client.prepare_transaction(value=price_in_wei)

        transaction = await self.domain_contract.functions.Register(
            domain
        ).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)
