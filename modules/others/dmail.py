from faker import Faker
from hashlib import sha256
from modules import Messenger
from mnemonic import Mnemonic
from random import choice, randint

from settings import GLOBAL_NETWORK, USE_PROXY
from utils.tools import gas_checker, repeater
from config import DMAIL_CONTRACT, DMAIL_ABI


class Dmail(Messenger):
    def __init__(self, client):
        self.client = client

    @staticmethod
    def generate_email():
        return f"{Faker().word()}{randint(1, 999999)}@{choice(['gmail.com', 'yahoo.com', 'outlook.com', 'icloud.com'])}"

    @staticmethod
    def generate_sentence():
        mnemo = Mnemonic("english")

        return mnemo.generate(128)

    @repeater
    @gas_checker
    async def send_message(self):
        close_session = False
        try:
            if GLOBAL_NETWORK == 9:
                await self.client.initialize_account()
                close_session = True

            self.client.logger.info(f'{self.client.info} Send mail from Dmail')

            email = self.generate_email()
            text = self.generate_sentence()

            to_address = sha256(f"{email}".encode()).hexdigest()
            message = sha256(f"{text}".encode()).hexdigest()

            self.client.logger.info(f'{self.client.info} Generated mail: {email} | Generated text: {text[:25]}...')
            if self.client.network.name == 'Starknet':
                dmail_contract = await self.client.get_contract(DMAIL_CONTRACT[self.client.network.name]['core'])

                stark_order = 3618502788666131213697322783095070105623107215331596699973092056135872020481
                to_address = int(to_address, 16) % (stark_order + 1)
                transaction = dmail_contract.functions["transaction"].prepare(to_address,
                                                                              to_address)
            else:

                dmail_contract = self.client.get_contract(DMAIL_CONTRACT[self.client.network.name]['core'],
                                                          DMAIL_ABI[self.client.network.name])

                transaction = await dmail_contract.functions.send_mail(
                    to_address,
                    message,
                ).build_transaction(await self.client.prepare_transaction())

            return await self.client.send_transaction(transaction)
        finally:
            if USE_PROXY and close_session:
                await self.client.session.close()
