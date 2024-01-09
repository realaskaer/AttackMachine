import json
import random

from modules import Bridge, Logger
from utils.tools import helper
from config import ORBITER_CONTRACTS, ORBITER_ABI, TOKENS_PER_CHAIN
from general_settings import GLOBAL_NETWORK
from settings import ORBITER_TOKEN_NAME
from web3 import AsyncWeb3


class Orbiter(Bridge, Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)
        Bridge.__init__(self, client)

    @staticmethod
    def get_maker_data(from_id:int, to_id:int, token_name: str):

        path = random.choice(['orbiter_maker1.json', 'orbiter_maker2.json'])
        with open(f'./data/services/{path}') as file:
            data = json.load(file)

        maker_data = data[f"{from_id}-{to_id}"][f"{token_name}-{token_name}"]

        bridge_data = {
            'maker': maker_data['makerAddress'],
            'fee': maker_data['tradingFee'],
            'min_amount': maker_data['minPrice'],
            'max_amount': maker_data['maxPrice'],
        } | ({'sender': maker_data['sender']} if GLOBAL_NETWORK == 9 else {})

        if bridge_data:
            return bridge_data
        raise RuntimeError(f'That bridge is not active!')

    @helper
    async def bridge(self, chain_from_id:int, private_keys:dict = None):
        if GLOBAL_NETWORK == 9 and chain_from_id == 9:
            await self.client.initialize_account()
        elif GLOBAL_NETWORK == 9 and chain_from_id != 9:
            await self.client.session.close()
            self.client = await self.client.initialize_evm_client(private_keys['evm_key'], chain_from_id)

        from_chain, to_chain, amount, to_chain_id = await self.client.get_bridge_data(chain_from_id, 'Orbiter')
        token_name = ORBITER_TOKEN_NAME

        bridge_info = f'{amount} {token_name} from {from_chain["name"]} to {to_chain["name"]}'
        self.logger_msg(*self.client.acc_info, msg=f'Bridge on Orbiter: {bridge_info}')

        bridge_data = self.get_maker_data(from_chain['id'], to_chain['id'], token_name)
        destination_code = 9000 + to_chain['id']
        decimals = await self.client.get_decimals(token_name)
        fee = int(float(bridge_data['fee']) * 10 ** decimals)
        min_price, max_price = bridge_data['min_amount'], bridge_data['max_amount']
        amount_in_wei = round(int(amount * 10 ** decimals), -4)
        full_amount = amount_in_wei + destination_code + fee

        if from_chain['name'] != 'Starknet' and to_chain['name'] == 'Starknet':

            contract = self.client.get_contract(ORBITER_CONTRACTS["evm_contracts"][self.client.network.name],
                                                ORBITER_ABI['evm_contract'])

            receiver = await self.get_address_for_bridge(private_keys['stark_key'], stark_key_type=True)

            transaction = [await contract.functions.transfer(
                AsyncWeb3.to_checksum_address(bridge_data['maker']),
                "0x03" + f'{receiver[2:]:0>64}'
            ).build_transaction(await self.client.prepare_transaction(value=full_amount))]

        elif from_chain['name'] == 'Starknet' and to_chain['name'] != 'Starknet':

            contract = await self.client.get_contract(ORBITER_CONTRACTS["stark_contract"])
            eth_address = TOKENS_PER_CHAIN['Starknet']['ETH']

            approve_call = self.client.get_approve_call(eth_address, ORBITER_CONTRACTS['stark_contract'],
                                                        unlim_approve=True)

            bridge_call = contract.functions["transferERC20"].prepare(
                eth_address,
                int(bridge_data['maker'], 16),
                full_amount,
                int(await self.get_address_for_bridge(private_keys['evm_key'], stark_key_type=False), 16)
            )

            transaction = approve_call, bridge_call
        elif token_name != 'ETH':
            if self.client.network.name in ['Polygon', 'Optimism']:
                contract = self.client.get_contract(TOKENS_PER_CHAIN[self.client.network.name]['USDC.e'])
            else:
                contract = self.client.get_contract(TOKENS_PER_CHAIN[self.client.network.name][token_name])

            transaction = [await contract.functions.transfer(
                AsyncWeb3.to_checksum_address(bridge_data['maker']),
                full_amount
            ).build_transaction(await self.client.prepare_transaction())]
        else:
            transaction = [(await self.client.prepare_transaction(value=full_amount)) | {
                'to': self.client.w3.to_checksum_address(bridge_data['maker'])
            }]

        if min_price <= amount <= max_price:
            if self.client.network.name in ['Polygon', 'Optimism']:
                balance_in_wei, _, _ = await self.client.get_token_balance('USDC.e')
            else:
                balance_in_wei, _, _ = await self.client.get_token_balance(token_name)

            if balance_in_wei > full_amount:

                if int(f"{full_amount}"[-4:]) != destination_code:
                    raise RuntimeError('Math problem in Python. Machine will save your money =)')

                old_balance_on_dst = await self.client.wait_for_receiving(to_chain_id, token_name=token_name,
                                                                          check_balance_on_dst=True)

                result = await self.client.send_transaction(*transaction)

                self.logger_msg(*self.client.acc_info,
                                msg=f"Bridge complete. Note: wait a little for receiving funds", type_msg='success')

                await self.client.wait_for_receiving(to_chain_id, old_balance_on_dst, token_name=token_name)

                return result

            else:
                raise RuntimeError(f'Insufficient balance!')
        else:
            raise RuntimeError(f"Limit range for bridge: {min_price} – {max_price} {token_name}!")
