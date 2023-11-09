from faker import Faker
from hashlib import sha256
from modules import Messenger
from mnemonic import Mnemonic
from random import choice, randint
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
        self.client.logger.info(f'{self.client.info} Dmail | Send mail from Dmail')

        email = self.generate_email()
        text = self.generate_sentence()

        to_address = sha256(f"{email}".encode()).hexdigest()
        message = sha256(f"{text}".encode()).hexdigest()

        self.client.logger.info(f'{self.client.info} Dmail | Generated mail: {email} | Generated text: {text[:25]}...')

        tx_params = await self.client.prepare_transaction()

        dmail_contract = self.client.get_contract(DMAIL_CONTRACT['core'], DMAIL_ABI)

        transaction = await dmail_contract.functions.send_mail(
            to_address,
            message,
        ).build_transaction(tx_params)

        tx_hash = await self.client.send_transaction(transaction)

        await self.client.verify_transaction(tx_hash)
