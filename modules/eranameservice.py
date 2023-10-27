from random import randint
from faker import Faker
from utils.tools import gas_checker, repeater
from config import ENS_CONTRACT, ENS_ABI
from modules import Client


class EraDomainService(Client):
    def __init__(self, account_number, private_key, network, proxy=None):
        super().__init__(account_number, private_key, network, proxy)
        self.domain_contract = self.get_contract(ENS_CONTRACT['era_name_service'], ENS_ABI)

    async def get_random_name(self):
        domain = f'{Faker().word()}{randint(100, 999999)}'

        check_domain = await self.domain_contract.functions._checkName(domain).call()

        if check_domain:
            return domain

        await self.get_random_name()

    @repeater
    @gas_checker
    async def mint_domain(self):

        _, _ = self.check_and_get_eth_for_deposit()

        self.logger.info(f'{self.info} Mint domain on ENS: 0.003 ETH')

        price_in_wei = 3000000000000000

        domain = await self.get_random_name()

        self.logger.info(f'{self.info} Generated domain: {domain}.era')

        tx_params = await self.prepare_transaction(value=price_in_wei)

        transaction = await self.domain_contract.functions.Register(
            domain
        ).build_transaction(tx_params)

        tx_hash = await self.send_transaction(transaction)

        await self.verify_transaction(tx_hash)

