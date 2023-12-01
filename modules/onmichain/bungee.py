import aiohttp
import random

from modules import Refuel, Logger
from settings import DESTINATION_BUNGEE_DATA
from utils.tools import gas_checker, repeater
from config import (
    BUNGEE_CONTRACTS,
    BUNGEE_REFUEL_ABI,
    BUNGEE_CHAINS_IDS,
    LAYERZERO_NETWORKS_DATA
)


class Bungee(Refuel, Logger):
    def __init__(self, client):
        super().__init__()
        self.client = client

        self.network = self.client.network.name
        self.refuel_contract = self.client.get_contract(BUNGEE_CONTRACTS[self.network]['gas_refuel'], BUNGEE_REFUEL_ABI)

    async def get_limits_data(self):
        url = 'https://refuel.socket.tech/chains'

        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, proxy=self.client.proxy) as response:
                if response.status == 200:
                    data = await response.json()
                    return [chain for chain in data['result'] if chain['name'] == self.network][0]
                raise RuntimeError(f'Bad request to Bungee API: {response.status}')

    @repeater
    @gas_checker
    async def refuel(self):
        dst_data = random.choice(list(DESTINATION_BUNGEE_DATA.items()))
        dst_chain_name, _, dst_native_name, _ = LAYERZERO_NETWORKS_DATA[dst_data[0]]
        dst_amount = self.client.round_amount(*dst_data[1])

        refuel_info = f'{dst_amount} {dst_native_name} to {dst_chain_name.capitalize()}'
        self.logger_msg(*self.client.acc_info, msg=f'Refuel on Bungee: {refuel_info}')

        refuel_limits_data = await self.get_limits_data()

        if refuel_limits_data['isSendingEnabled']:
            dst_chain_id = BUNGEE_CHAINS_IDS[f'{dst_chain_name}']
            limits_dst_chain_data = {}

            for chain_limits in refuel_limits_data['limits']:
                if chain_limits['chainId'] == dst_chain_id:
                    limits_dst_chain_data = chain_limits
                    break

            if 'isEnabled' in limits_dst_chain_data and limits_dst_chain_data['isEnabled']:
                min_amount_in_wei = int(limits_dst_chain_data['minAmount'])
                max_amount_in_wei = int(limits_dst_chain_data['maxAmount'])

                min_amount = round(self.client.w3.from_wei(min_amount_in_wei, 'ether') * 100000) / 100000
                max_amount = round(self.client.w3.from_wei(max_amount_in_wei, 'ether') * 100000) / 100000

                amount_in_wei = int(dst_amount * 10 ** 18)

                if min_amount_in_wei <= amount_in_wei <= max_amount_in_wei:

                    if await self.client.w3.eth.get_balance(self.client.address) >= amount_in_wei:

                        tx_params = await self.client.prepare_transaction(value=amount_in_wei)

                        transaction = await self.refuel_contract.functions.depositNativeToken(
                            dst_chain_id,
                            self.client.address
                        ).build_transaction(tx_params)

                        return await self.client.send_transaction(transaction)

                    else:
                        raise RuntimeError("Insufficient balance!")
                else:
                    raise RuntimeError(f'Limit range for refuel: {min_amount} - {max_amount} ETH!')
            else:
                raise RuntimeError('Destination chain refuel is not active!')
        else:
            raise RuntimeError('Source chain refuel is not active!')
