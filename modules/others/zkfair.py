from datetime import datetime
from eth_account.messages import encode_defunct
from config import ZKFAIR_ABI
from modules import Logger, Aggregator
from settings import ZKFAIR_CLAIM_REFUND_PHASES
from utils.tools import helper


class ZKFair(Logger, Aggregator):
    def __init__(self, client):
        Logger.__init__(self)
        Aggregator.__init__(self, client)

    async def claim_refund(self):
        timestamp, api_signature = self.get_authentication_data()

        url_proof = 'https://airdrop.zkfair.io/api/refund_merkle'
        url_refund = 'https://airdrop.zkfair.io/api/refundable'

        for phase in ZKFAIR_CLAIM_REFUND_PHASES:
            params_proof = {
                'address': self.client.address,
                'phase': phase,
                'API-SIGNATURE': api_signature,
                'TIMESTAMP': timestamp
            }

            params_refund = {
                'address': self.client.address,
                'API-SIGNATURE': api_signature,
                'TIMESTAMP': timestamp
            }

            try:
                proof = (await self.make_request(url=url_proof, params=params_proof))['data']['proof']
                refund_data = (await self.make_request(url=url_refund, params=params_refund))['data'][f"phase{phase}"]
                refund_index = int(refund_data['refund_index'])
                refund_in_wei = int(refund_data['account_refund'])
                refund_contract_address = refund_data['refund_contract_address']
            except:
                self.logger_msg(
                    *self.client.acc_info,
                    msg=f'Available to refund in phase {phase}: 0 USDC', type_msg='warning')
                continue

            self.logger_msg(
                *self.client.acc_info,
                msg=f'Available to refund in phase {phase}: {refund_in_wei / 10 ** 18:.3f} USDC', type_msg='success')

            refund_contract = self.client.get_contract(refund_contract_address, ZKFAIR_ABI)

            transaction = await refund_contract.functions.claim(
                refund_index,
                refund_in_wei,
                proof
            ).build_transaction(await self.client.prepare_transaction())

            await self.client.send_transaction(transaction)

        return True

    def get_authentication_data(self):
        current_time = datetime.utcnow()
        formatted_time = current_time.isoformat(timespec='milliseconds') + 'Z'

        text = f"{formatted_time}GET/api/airdrop?address={self.client.address}"

        text_hex = "0x" + text.encode('utf-8').hex()
        text_encoded = encode_defunct(hexstr=text_hex)
        signature = self.client.w3.eth.account.sign_message(text_encoded,
                                                            private_key=self.client.private_key).signature

        return formatted_time, self.client.w3.to_hex(signature)

    @helper
    async def claim_drop(self):
        timestamp, api_signature = self.get_authentication_data()

        url_proof = 'https://airdrop.zkfair.io/api/airdrop_merkle'
        url_airdrop = 'https://airdrop.zkfair.io/api/airdrop'

        params_proof = {
            'address': self.client.address,
            'API-SIGNATURE': api_signature,
            'TIMESTAMP': timestamp
        }

        params_airdrop = {
            'address': self.client.address,
            'API-SIGNATURE': api_signature,
            'TIMESTAMP': timestamp
        }

        proof_data = (await self.make_request(url=url_proof, params=params_proof))
        airdrop_data = (await self.make_request(url=url_airdrop, params=params_airdrop))

        if proof_data['resultCode'] == 0 and airdrop_data['resultCode'] == 0:
            proof = proof_data['data']['proof']
            airdrop_index = int(airdrop_data['data']['index'])
            airdrop_in_wei = int(airdrop_data['data']['account_profit'])
            airdrop_contract_address = airdrop_data['data']['contract_address']

            self.logger_msg(
                *self.client.acc_info,
                msg=f'Available to claim: {airdrop_in_wei / 10 ** 18:.3f} ZKF', type_msg='success')

            airdrop_contract = self.client.get_contract(airdrop_contract_address, ZKFAIR_ABI)

            transaction = await airdrop_contract.functions.claim(
                int(airdrop_index),
                int(airdrop_in_wei),
                proof
            ).build_transaction(await self.client.prepare_transaction())

            await self.client.send_transaction(transaction)

        else:
            self.logger_msg(
                *self.client.acc_info,
                msg=f'Not available to claim', type_msg='warning')

        return True
