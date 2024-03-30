import os
import time
import json
import base64
import random
import asyncio

from config import RHINO_ABI
from modules import Bridge, Logger, Client
from datetime import datetime, timezone

from modules.interfaces import SoftwareException
from utils.tools import sleep
from eth_account.messages import encode_defunct, encode_structured_data
from utils.stark_signature.stark_singature import sign, pedersen_hash, EC_ORDER, private_to_stark_key
from utils.stark_signature.eth_coder import encrypt_with_public_key, decrypt_with_private_key, get_public_key

REGISTER_DATA = {
    "types": {
        "EIP712Domain": [
            {"name": "name", "type": "string"},
            {"name": "version", "type": "string"}
        ],
        "rhino.fi": [
            {"type": "string", "name": "action"},
            {"type": "string", "name": "onlySignOn"}
        ]
    },
    "domain": {
        "name": "rhino.fi",
        "version": "1.0.0"
    },
    "primaryType": "rhino.fi",
    "message": {
        "action": "Access your rhino.fi account",
        "onlySignOn": "app.rhino.fi"
    }
}


class Rhino(Bridge, Logger):
    def __init__(self, client: Client):
        self.client = client
        Logger.__init__(self)
        Bridge.__init__(self, client)
        self.nonce, self.signature = None, None

    def get_authentication_data(self):
        date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S")
        nonce = f"{time.time():.3f}"

        text = (f"To protect your rhino.fi privacy we ask you to sign in with your wallet to see your data.\n"
                f"Signing in on {date} GMT. For your safety, only sign this message on rhino.fi!")

        nonse_str = f"v3-{nonce}"
        text_hex = "0x" + text.encode('utf-8').hex()
        text_encoded = encode_defunct(hexstr=text_hex)
        signature = self.client.w3.eth.account.sign_message(text_encoded,
                                                            private_key=self.client.private_key).signature

        return nonse_str, self.client.w3.to_hex(signature)

    def make_headers(self):
        data_to_headers = f'{{"signature":"{self.signature}","nonce":"{self.nonce}"}}'

        headers = {
            "Accept":"application/json",
            "Accept-Encoding":"utf-8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Content-Type":"application/json",
            "Origin":"https://app.rhino.fi",
            "Referer":"https://app.rhino.fi/",
            "Sec-Ch-Ua":'"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
            "Sec-Ch-Ua-Mobile":"?0",
            "Sec-Ch-Ua-Platform":'"Windows"',
            "Sec-Fetch-Dest":"empty",
            "Sec-Fetch-Mode":"cors",
            "Sec-Fetch-Site":"same-site",
            "Authorization": f"EcRecover {base64.b64encode(data_to_headers.encode('utf-8')).decode('utf-8')}"
        }

        return headers

    @staticmethod
    def create_stark_key(dtk_private_key):
        stark_key = private_to_stark_key(int(f"0x{dtk_private_key}", 16) % EC_ORDER)

        return f"0{hex(stark_key)[2:]}"

    def create_dtk(self):
        dtk = os.urandom(32).hex()

        text_encoded = encode_structured_data(REGISTER_DATA)
        sing_data = self.client.w3.eth.account.sign_message(text_encoded,
                                                            private_key=self.client.private_key).signature

        encryption_key = self.client.w3.keccak(f"{sing_data.hex()}".encode('utf-8'))

        public_key = get_public_key(encryption_key).hex()

        encrypted_message = encrypt_with_public_key(public_key, json.dumps({"data": dtk}))

        return dtk, encrypted_message

    async def get_user_config(self):

        url = "https://api.rhino.fi/v1/trading/r/getUserConf"

        data = {
            'nonce': self.nonce,
            'signature': self.signature
        }

        while True:
            try:
                data = await self.make_request(method='POST', url=url, headers=self.headers, json=data)
                return data
            except:
                self.logger_msg(*self.client.acc_info, msg=f"Get bad API data", type_msg='warning')
                await asyncio.sleep(5)

    async def get_vault_id(self, token_name):

        url = "https://api.rhino.fi/v1/trading/r/getVaultId"

        data = {
            'nonce': self.nonce,
            'signature': self.signature,
            'token': token_name
        }

        return await self.make_request(method='POST', url=url, headers=self.headers, json=data)

    async def reg_new_acc(self):

        url = 'https://api.rhino.fi/v1/trading/w/register'

        dtk, encrypted_trading_key = self.create_dtk()
        stark_public_key_x = self.create_stark_key(dtk)

        data = {
            "encryptedTradingKey": {
                "dtk": encrypted_trading_key,
                "dtkVersion": "v3"
            },
            "meta":
                {
                    "walletType": "metamask",
                    "campaign": None,
                    "referer": None,
                    "platform": "DESKTOP",
                },
            "nonce": self.nonce,
            "signature": self.signature,
            "starkKey": stark_public_key_x,
        }

        return await self.make_request(method='POST', url=url, headers=self.headers, json=data)

    async def recover_trading_key(self):

        url = 'https://api.rhino.fi/v1/trading/r/recoverTradingKey'

        data = {
            "nonce": self.nonce,
            "signature": self.signature,
            "meta": {
                "ethAddress": self.client.address,
            }
        }

        return await self.make_request(method='POST', url=url, headers=self.headers, json=data)

    async def recover_dtk(self):
        encrypted_trading_key = (await self.recover_trading_key())['encryptedTradingKey']
        text_encoded = encode_structured_data(REGISTER_DATA)
        sing_data = self.client.w3.eth.account.sign_message(text_encoded,
                                                            private_key=self.client.private_key).signature
        encryption_private_key = self.client.w3.keccak(f"{sing_data.hex()}".encode('utf-8')).hex()

        dtk = decrypt_with_private_key(encryption_private_key, encrypted_trading_key)

        return json.loads(dtk)['data']

    async def get_vault_id_and_stark_key(self, token_name, deversifi_address):

        url = "https://api.rhino.fi/v1/trading/r/vaultIdAndStarkKey"

        headers = self.make_headers()

        params = {
            "token": token_name,
            "targetEthAddress": deversifi_address,
        }

        return await self.make_request(method="GET", url=url, headers=headers, params=params)

    async def get_user_balance(self, token_name:str = 'ETH'):

        data = {
            "nonce": self.nonce,
            "signature": self.signature,
            "token": token_name,
            "fields": [
                "balance",
                "available",
                "updatedAt"
            ]
        }

        url = "https://api.rhino.fi/v1/trading/r/getBalance"

        response = await self.make_request(method="POST", url=url, headers=self.headers, json=data)
        if response:
            return response[0]['available']
        return 0

    async def get_stark_signature(self, amount_in_wei, expiration_timestamp, tx_nonce, receiver_public_key,
                                  receiver_vault_id, sender_vault_id, token_address):

        packed_message = 1  # instruction_type
        packed_message = (packed_message << 31) + int(sender_vault_id)
        packed_message = (packed_message << 31) + int(receiver_vault_id)
        packed_message = (packed_message << 63) + int(amount_in_wei)
        packed_message = (packed_message << 63) + 0
        packed_message = (packed_message << 31) + int(tx_nonce)
        packed_message = (packed_message << 22) + int(expiration_timestamp)

        msg_hash = pedersen_hash(pedersen_hash(int(token_address, 16), int(receiver_public_key, 16)),
                                 int(packed_message))

        stark_dtk_private_key = int(await self.recover_dtk(), 16) % EC_ORDER

        tx_signature = sign(msg_hash=msg_hash, priv_key=stark_dtk_private_key)
        return hex(tx_signature[0]), hex(tx_signature[1])

    async def deposit_to_rhino(self, amount, token_name, token_address, source_chain_info: dict):
        self.logger_msg(
            *self.client.acc_info, msg=f"Deposit {amount} {token_name} from {self.client.network.name} to Rhino")

        if source_chain_info['enabled']:
            source_chain_address = self.client.w3.to_checksum_address(source_chain_info['contractAddress'])

            if token_name != self.client.token:
                amount_in_wei = self.client.to_wei(amount, await self.client.get_decimals(token_name=token_name))
                await self.client.check_for_approved(token_address, source_chain_address, amount_in_wei)
                contract = self.client.get_contract(source_chain_address, RHINO_ABI['router'])

                transaction = await contract.functions.deposit(
                    token_address,
                    amount_in_wei
                ).build_transaction(await self.client.prepare_transaction())

            else:
                amount_in_wei = self.client.to_wei(amount)
                transaction = await self.client.prepare_transaction(value=amount_in_wei) | {
                    'data': "0xdb6b5246",
                    'to': source_chain_address
                }

            return await self.client.send_transaction(transaction)

        raise SoftwareException(f"Deposit from {self.client.network.name} is not active!")

    async def withdraw_from_rhino(self, rhino_user_config, amount, token_name, chain_to_name, need_refund:bool = False):
        decimals = await self.client.get_decimals(token_name) if token_name != 'ETH' else 8
        while True:
            await asyncio.sleep(4)
            if int(amount * 10 ** decimals) <= int(await self.get_user_balance(token_name)) or need_refund:
                self.logger_msg(*self.client.acc_info, msg=f"Funds have been received to Rhino", type_msg='success')
                break
            self.logger_msg(
                *self.client.acc_info, msg=f"Wait a little, while the funds come into Rhino", type_msg='warning')
            await asyncio.sleep(1)
            await sleep(self, 90, 120)

        if need_refund:
            amount = int(await self.get_user_balance(token_name)) / 10 ** 8

        chain_name_log = chain_to_name.capitalize()
        self.logger_msg(*self.client.acc_info, msg=f"Withdraw {amount} {token_name} from Rhino to {chain_name_log}")

        url = "https://api.rhino.fi/v1/trading/bridgedWithdrawals"

        deversifi_address = rhino_user_config["DVF"]['deversifiAddress']
        receiver_data = (await self.get_vault_id_and_stark_key(token_name, deversifi_address)).values()
        receiver_vault_id, receiver_public_key = receiver_data

        sender_public_key = rhino_user_config['starkKeyHex']
        sender_vault_id = await self.get_vault_id(token_name)
        token_address = rhino_user_config['tokenRegistry'][token_name]['starkTokenId']

        expiration_timestamp = int(time.time() / 3600) + 4320
        payload_nonce = random.randint(1, 2**53 - 1)
        tx_nonce = random.randint(1, 2**31 - 1)
        amount_in_wei = int(amount * 10 ** decimals)

        r_signature, s_signature = await self.get_stark_signature(amount_in_wei, expiration_timestamp, tx_nonce,
                                                                  receiver_public_key,receiver_vault_id,
                                                                  sender_vault_id, token_address)

        headers = self.make_headers()

        payload = {
            "chain": chain_to_name,
            "token": token_name,
            "amount": f"{amount_in_wei}",
            "tx": {
                "amount": amount_in_wei,
                "senderPublicKey": sender_public_key,
                "receiverPublicKey": receiver_public_key,
                "receiverVaultId": receiver_vault_id,
                "senderVaultId": sender_vault_id,
                "signature": {
                    "r": r_signature,
                    "s": s_signature
                },
                "token": token_address,
                "type": "TransferRequest",
                "nonce": tx_nonce,
                "expirationTimestamp": expiration_timestamp
            },
            "nonce": payload_nonce,
            "recipientEthAddress": self.client.address,
            "isBridge": False,
        }

        await self.make_request(method='POST', url=url, headers=headers, json=payload)

        self.logger_msg(*self.client.acc_info,
                        msg=f"Bridge complete. Note: wait a little for receiving funds", type_msg='success')

    async def bridge(self, chain_from_id: int, bridge_data: tuple, need_check: bool = False):
        (from_chain, to_chain, amount, to_chain_id, from_token_name,
         to_token_name, from_token_address, to_token_address) = bridge_data

        if need_check:
            return 0

        self.nonce, self.signature = self.get_authentication_data()
        self.logger_msg(*self.client.acc_info, msg=f"Check previous registration on Rhino")

        rhino_user_config = await self.get_user_config()

        if not rhino_user_config['isRegistered']:
            self.logger_msg(*self.client.acc_info, msg=f"New user on Rhino, make registration")
            await self.reg_new_acc()

            self.logger_msg(*self.client.acc_info, msg=f"Successfully registered on Rhino", type_msg='success')
            rhino_user_config = await self.get_user_config()
        else:

            self.logger_msg(*self.client.acc_info, msg=f"Already registered on Rhino", type_msg='success')

        source_chain_info = rhino_user_config['DVF']['bridgeConfigPerChain'][from_chain]

        old_balance_on_dst = await self.client.wait_for_receiving(
            to_chain_id, check_balance_on_dst=True, token_name=to_token_name, token_address=to_token_address
        )

        await self.deposit_to_rhino(amount, from_token_name, from_token_address, source_chain_info)

        await self.withdraw_from_rhino(rhino_user_config, amount, to_token_name, to_chain)

        return await self.client.wait_for_receiving(
            to_chain_id, old_balance_on_dst, token_name=to_token_name, token_address=to_token_address
        )

    async def recovery_funds(self):
        from settings import RHINO_CHAIN_ID_TO
        from settings import RHINO_TOKEN_NAME
        from config import RHINO_CHAIN_INFO

        self.nonce, self.signature = self.get_authentication_data()
        rhino_user_config = await self.get_user_config()
        _, to_token_name = RHINO_TOKEN_NAME
        to_chain = RHINO_CHAIN_INFO[random.choice(RHINO_CHAIN_ID_TO)]

        await self.withdraw_from_rhino(rhino_user_config, 0, to_token_name, to_chain, need_refund=True)
