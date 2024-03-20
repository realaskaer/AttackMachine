import json
import random

from modules import Bridge, Logger
from modules.interfaces import BridgeExceptionWithoutRetry, SoftwareExceptionWithoutRetry
from web3 import AsyncWeb3


class Orbiter(Bridge, Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)
        Bridge.__init__(self, client)

    @staticmethod
    def get_maker_data(from_id:int, to_id:int, token_name: str):

        paths = ['orbiter_maker1.json', 'orbiter_maker2.json', 'orbiter_maker3.json',
                 'orbiter_maker4.json', 'orbiter_maker5.json']
        for path in paths:
            try:
                with open(f'./data/services/{path}') as file:
                    data = json.load(file)

                maker_data = data[f"{from_id}-{to_id}"][f"{token_name}-{token_name}"]

                bridge_data = {
                    'maker': maker_data['makerAddress'],
                    'fee': maker_data['tradingFee'],
                    'min_amount': maker_data['minPrice'],
                    'max_amount': maker_data['maxPrice'],
                }

                if bridge_data:
                    return bridge_data
            except KeyError:
                pass

        raise BridgeExceptionWithoutRetry(f'That bridge is not active!')

    async def bridge(self, chain_from_id: int, bridge_data: tuple, need_check: bool = False):
        (from_chain, to_chain, amount, to_chain_id, from_token_name,
         to_token_name, from_token_address, to_token_address) = bridge_data

        if not need_check:
            bridge_info = f'{amount} {from_token_name} from {from_chain["name"]} to {to_chain["name"]}'
            self.logger_msg(*self.client.acc_info, msg=f'Bridge on Orbiter: {bridge_info}')

        bridge_data = self.get_maker_data(from_chain['id'], to_chain['id'], from_token_name)
        destination_code = 9000 + to_chain['id']
        decimals = await self.client.get_decimals(token_address=from_token_address)
        fee = int(float(bridge_data['fee']) * 10 ** decimals)
        amount_in_wei = self.client.to_wei(amount, decimals)
        full_amount = int(round(amount_in_wei + fee, -4) + destination_code)

        if need_check:
            return round(float(fee / 10 ** decimals), 6)

        min_price, max_price = bridge_data['min_amount'], bridge_data['max_amount']

        if from_token_name != self.client.network.token:
            contract = self.client.get_contract(from_token_address)

            transaction = await contract.functions.transfer(
                AsyncWeb3.to_checksum_address(bridge_data['maker']),
                full_amount
            ).build_transaction(await self.client.prepare_transaction())
        else:
            transaction = (await self.client.prepare_transaction(value=full_amount)) | {
                'to': self.client.w3.to_checksum_address(bridge_data['maker'])
            }

        if min_price <= amount <= max_price:
            if int(f"{full_amount}"[-4:]) != destination_code:
                raise SoftwareExceptionWithoutRetry('Math problem in Python. Machine will save your money =)')

            old_balance_on_dst = await self.client.wait_for_receiving(
                token_address=to_token_address, token_name=to_token_name, chain_id=to_chain_id,
                check_balance_on_dst=True
            )

            await self.client.send_transaction(transaction)

            self.logger_msg(
                *self.client.acc_info, msg=f"Bridge complete. Note: wait a little for receiving funds",
                type_msg='success'
            )

            return await self.client.wait_for_receiving(
                token_address=to_token_address, token_name=to_token_name, old_balance=old_balance_on_dst,
                chain_id=to_chain_id
            )

        else:
            raise BridgeExceptionWithoutRetry(f"Limit range for bridge: {min_price} – {max_price} {from_token_name}!")
