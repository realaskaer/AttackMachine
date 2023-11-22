import os
import time
import json
import base64
import random
import asyncio

from config import TOKENS_PER_CHAIN
from modules import Bridge
from datetime import datetime, timezone

from settings import GLOBAL_NETWORK, USE_PROXY
from utils.tools import gas_checker, sleep
from eth_account.messages import encode_defunct
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


class Rhino(Bridge):
    def __init__(self, client):
        super().__init__(client)

        self.nonce, self.signature = None, None
        self.evm_client = None

    def get_authentication_data(self):
        date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S")
        nonce = f"{time.time():.3f}"

        text = (f"To protect your rhino.fi privacy we ask you to sign in with your wallet to see your data.\n"
                f"Signing in on {date} GMT. For your safety, only sign this message on rhino.fi!")

        nonse_str = f"v3-{nonce}"
        text_hex = "0x" + text.encode('utf-8').hex()
        text_encoded = encode_defunct(hexstr=text_hex)
        signature = self.evm_client.w3.eth.account.sign_message(text_encoded,
                                                                private_key=self.evm_client.private_key).signature

        return nonse_str, self.evm_client.w3.to_hex(signature)

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
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
                         " Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
            "Authorization": f"EcRecover {base64.b64encode(data_to_headers.encode('utf-8')).decode('utf-8')}"
        }

        return headers

    @staticmethod
    def create_stark_key(dtk_private_key):
        stark_key = private_to_stark_key(int(f"0x{dtk_private_key}", 16) % EC_ORDER)

        return f"0{hex(stark_key)[2:]}"

    def create_dtk(self):
        dtk = os.urandom(32).hex()

        sing_data = self.evm_client.w3.eth.account.sign_typed_data(self.evm_client.private_key,
                                                                   full_message=REGISTER_DATA).signature

        encryption_key = self.evm_client.w3.keccak(f"{sing_data.hex()}".encode('utf-8'))

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
                self.evm_client.logger.warning(f"{self.evm_client.info} Rhino | Get bad API data")
                await asyncio.sleep(5)

    async def get_vault_id(self):

        url = "https://api.rhino.fi/v1/trading/r/getVaultId"

        data = {
            'nonce': self.nonce,
            'signature': self.signature,
            'token': 'ETH'
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
                "ethAddress": self.evm_client.address,
            }
        }

        return await self.make_request(method='POST', url=url, headers=self.headers, json=data)

    async def recover_dtk(self):
        encrypted_trading_key = (await self.recover_trading_key())['encryptedTradingKey']
        sing_data = self.evm_client.w3.eth.account.sign_typed_data(self.evm_client.private_key,
                                                                   full_message=REGISTER_DATA).signature
        encryption_private_key = self.evm_client.w3.keccak(f"{sing_data.hex()}".encode('utf-8')).hex()

        dtk = decrypt_with_private_key(encryption_private_key, encrypted_trading_key)

        return json.loads(dtk)['data']

    async def get_vault_id_and_stark_key(self, deversifi_address):

        url = "https://api.rhino.fi/v1/trading/r/vaultIdAndStarkKey"

        headers = self.make_headers()

        params = {
            "token": 'ETH',
            "targetEthAddress": deversifi_address,
        }

        return await self.make_request(method="GET", url=url, headers=headers, params=params)

    async def get_user_balance(self):

        data = {
            "nonce": self.nonce,
            "signature": self.signature,
            "token": "ETH",
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

    @gas_checker
    async def deposit_to_rhino(self, amount, source_chain_info, chain_from_name, chain_to_name, private_keys):
        logger_info = f"Deposit {amount} ETH to Rhino"
        self.client.logger_msg(self.client.account_name, self.client.private_key, logger_info)

        if source_chain_info['enabled']:
            source_chain_address = source_chain_info['contractAddress']
            amount_in_wei = int(amount * 10 ** 18)

            if chain_from_name == 'STARKNET' and chain_to_name != 'STARKNET':
                approve_call = self.client.get_approve_call(TOKENS_PER_CHAIN['Starknet']['ETH'],
                                                            int(source_chain_info['contractAddress'], 16),
                                                            amount_in_wei)

                rhino_contract = await self.client.get_contract(int(source_chain_info['contractAddress'], 16))
                deposit_call = rhino_contract.functions['deposit'].prepare(
                    TOKENS_PER_CHAIN['Starknet']['ETH'],
                    amount_in_wei,
                    int(await self.get_address_for_bridge(private_keys['evm_key'], stark_key_type=False), 16)
                )

                transaction = approve_call, deposit_call
            else:
                transaction = [await self.client.prepare_transaction(value=amount_in_wei) | {
                    'data': "0xdb6b5246",
                    'to': self.client.w3.to_checksum_address(source_chain_address)
                }]

            await self.client.send_transaction(*transaction)

    async def withdraw_from_rhino(self, rhino_user_config, amount, chain_name, account_info, dst_address):

        while True:
            await asyncio.sleep(4)
            if int(amount * 10 ** 8) <= int(await self.get_user_balance()):
                self.client.logger_msg(*account_info, f"Funds have been received to Rhino", 'success')
                break
            self.client.logger_msg(*account_info, f"Wait a little, while the funds come into Rhino", 'warning')
            await asyncio.sleep(1)
            await sleep(self, 90, 120)

        logger_info = *account_info, f"Withdraw {amount} ETH from Rhino to {chain_name.capitalize()}"
        self.client.logger_msg(*logger_info)

        url = "https://api.rhino.fi/v1/trading/bridgedWithdrawals"

        deversifi_address = rhino_user_config["DVF"]['deversifiAddress']
        receiver_vault_id, receiver_public_key = (await self.get_vault_id_and_stark_key(deversifi_address)).values()

        sender_public_key = rhino_user_config['starkKeyHex']
        sender_vault_id = await self.get_vault_id()
        token_address = rhino_user_config['tokenRegistry']['ETH']['starkTokenId']

        expiration_timestamp = int(time.time() / 3600) + 4320
        payload_nonce = random.randint(1, 2**53 - 1)
        tx_nonce = random.randint(1, 2**31 - 1)
        amount_in_wei = int(amount * 10 ** 8)

        r_signature, s_signature = await self.get_stark_signature(amount_in_wei, expiration_timestamp, tx_nonce,
                                                                  receiver_public_key,receiver_vault_id,
                                                                  sender_vault_id, token_address)

        headers = self.make_headers()

        payload = {
            "chain": chain_name,
            "token": "ETH",
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
            "recipientEthAddress": dst_address,
            "isBridge": False,
        }

        await self.make_request(method='POST', url=url, headers=headers, json=payload)

        self.client.logger_msg(*account_info, f"Withdraw from on Rhino compete", 'success')

    async def bridge(self, chain_from_id:int, private_keys:dict = None, help_okx:bool = False, help_network_id:int = 1):
        close_session = False
        try:
            # if GLOBAL_NETWORK == 9:
            #     self.evm_client = await self.initialize_evm_client(private_keys['evm_key'], chain_from_id)
            #     close_session = True
            #
            #     if chain_from_id != 9:
            #         self.init_client = await self.initialize_init_client(private_keys['stark_key'])
            #
            #     await self.init_client.initialize_account()
            # else:
            #     self.evm_client = self.init_client
            if GLOBAL_NETWORK == 9 and chain_from_id == 9:
                await self.client.initialize_account()
                close_session = True
            if GLOBAL_NETWORK == 9:
                self.evm_client = await self.initialize_evm_client(private_keys['evm_key'], chain_from_id)

            self.nonce, self.signature = self.get_authentication_data()
            account_info = self.client.account_name, self.client.private_key
            self.client.logger_msg(*account_info, f"Check previous registration on Rhino")

            rhino_user_config = await self.get_user_config()

            if not rhino_user_config['isRegistered']:
                await asyncio.sleep(1)

                self.client.logger_msg(*account_info, f"New user on Rhino, make registration")
                await self.reg_new_acc()

                await asyncio.sleep(1)

                self.client.logger_msg(*account_info, f"Successfully registered on Rhino", 'success')
                rhino_user_config = await self.get_user_config()
            else:
                await asyncio.sleep(1)

                self.client.logger_msg(*account_info, f"Already registered on Rhino", 'success')

            await asyncio.sleep(1)

            chain_from_name, chain_to_name, amount = await self.client.get_bridge_data(chain_from_id, help_okx,
                                                                                       help_network_id, 'Rhino')

            _, balance, _ = await self.client.get_token_balance()

            if amount < balance:

                source_chain_info = rhino_user_config['DVF']['bridgeConfigPerChain'][chain_from_name]

                await asyncio.sleep(1)

                await self.deposit_to_rhino(amount, source_chain_info, chain_from_name, chain_to_name, private_keys)

                await asyncio.sleep(1)

                dst_address = await self.get_address_for_bridge(private_keys['evm_key'], False)
                if chain_to_name == 'STARKNET':
                    dst_address = await self.get_address_for_bridge(private_keys['stark_key'], True)
                amount = 0.01
                await self.withdraw_from_rhino(rhino_user_config, amount, chain_to_name, account_info, dst_address)

                return True
            else:
                self.client.logger_msg(*account_info, f"Insufficient balance in {self.client.network.name}", 'error')
        except Exception as error:
            self.client.logger.error(f"{self.client.info} Error in Rhino: {error}")
        finally:
            if USE_PROXY and close_session:
                await self.client.session.close()

    async def initialize_evm_client(self, private_key, chain_id):
        from modules import Client
        from functions import get_network_by_chain_id
        evm_client = Client('Bridge', private_key,
                            get_network_by_chain_id(chain_id), self.client.proxy_init)
        return evm_client

    async def initialize_init_client(self, private_key):
        from modules import StarknetClient
        from utils.networks import StarknetRPC
        stark_client = StarknetClient('Bridge', private_key, StarknetRPC, self.client.proxy_init)
        return stark_client
