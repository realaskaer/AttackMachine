import json
import random

from modules import Refuel, Logger
from modules.interfaces import SoftwareException, Bridge, BridgeExceptionWithoutRetry
from settings import DST_CHAIN_BUNGEE_REFUEL
from utils.tools import gas_checker, helper
from config import (
    BUNGEE_CONTRACTS,
    BUNGEE_REFUEL_ABI,
    BUNGEE_CHAINS_IDS,
    LAYERZERO_NETWORKS_DATA,
    CHAIN_NAME_FROM_ID, ETH_MASK
)


class Bungee(Refuel, Bridge, Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)
        Bridge.__init__(self, client)

        self.network = self.client.network.name
        self.refuel_contract = self.client.get_contract(BUNGEE_CONTRACTS[self.network]['gas_refuel'], BUNGEE_REFUEL_ABI)

    async def get_limits_data(self):
        url = 'https://refuel.socket.tech/chains'

        async with self.client.session.get(url=url) as response:
            if response.status == 200:
                data = await response.json()
                return [chain for chain in data['result'] if chain['name'] == self.network][0]
            raise SoftwareException(f'Bad request to Bungee API: {response.status}')

    @helper
    @gas_checker
    async def refuel(self):
        dst_data = random.choice(list(DST_CHAIN_BUNGEE_REFUEL.items()))
        dst_chain_name, _, dst_native_name, _ = LAYERZERO_NETWORKS_DATA[dst_data[0]]
        dst_amount = self.client.round_amount(*dst_data[1])

        refuel_info = f'{dst_amount} {self.client.network.token} from {self.client.network.name} to {dst_chain_name}'
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

                amount_in_wei = self.client.to_wei(dst_amount)

                if min_amount_in_wei <= amount_in_wei <= max_amount_in_wei:

                    if await self.client.w3.eth.get_balance(self.client.address) >= amount_in_wei:

                        tx_params = await self.client.prepare_transaction(value=amount_in_wei)

                        transaction = await self.refuel_contract.functions.depositNativeToken(
                            dst_chain_id,
                            self.client.address
                        ).build_transaction(tx_params)

                        return await self.client.send_transaction(transaction)

                    else:
                        raise SoftwareException("Insufficient balance!")
                else:
                    raise SoftwareException(f'Limit range for refuel: {min_amount} - {max_amount} ETH!')
            else:
                raise SoftwareException('Destination chain refuel is not active!')
        else:
            raise SoftwareException('Source chain refuel is not active!')

    async def get_quote(self, to_chain_id, from_token_address, to_token_address, amount):
        url = 'https://api.socket.tech/v2/quote'

        params = {
            "fromChainId": self.client.chain_id,
            "toChainId": to_chain_id,
            "fromTokenAddress": from_token_address,
            "toTokenAddress": to_token_address,
            "fromAmount": amount,
            "userAddress": self.client.address,
            "singleTxOnly": "true",
            "bridgeWithGas": "false",
            "sort": "output",
            "defaultSwapSlippage": 0.5,
            "bridgeWithInsurance": "true",
            "isContractCall": "false",
            "showAutoRoutes": "false",
        }

        response = await self.make_request(url=url, params=params, headers=self.headers)

        if response['success']:
            return response['result']['routes'][0]
        raise BridgeExceptionWithoutRetry(f'Bad request to Bungee API: {await response.text()}')

    async def build_tx(self, route:dict):
        url = 'https://api.socket.tech/v2/build-tx'

        payload = {
            'route': route
        }

        response = await self.make_request(method="POST", url=url, json=payload, headers=self.headers)

        if response['success']:
            tx_data = response['result']['txData']
            contract_address = response['result']['txTarget']

            return tx_data, contract_address
        raise BridgeExceptionWithoutRetry(f'Bad request to Bungee API: {await response.text()}')

    async def bridge(self, chain_from_id: int, bridge_data: tuple, need_check: bool = False):
        from_chain, to_chain, amount, to_chain_id, token_name, from_token_address, to_token_address = bridge_data

        if not need_check:
            bridge_info = f'{self.client.network.name} -> {token_name} {CHAIN_NAME_FROM_ID[to_chain]}'
            self.logger_msg(*self.client.acc_info, msg=f'Bridge on Bungee: {amount} {token_name} {bridge_info}')

        amount_in_wei = self.client.to_wei(amount)

        if token_name == 'ETH':
            from_token_address = ETH_MASK
            to_token_address = ETH_MASK

        if need_check:
            return round(float(amount), 6)

        route_data = await self.get_quote(to_chain, from_token_address, to_token_address, amount_in_wei)

        tx_data, to_address = await self.build_tx(route_data)

        transaction = await self.client.prepare_transaction(value=amount_in_wei) | {
            'to': to_address,
            'data': tx_data
        }

        old_balance_on_dst = await self.client.wait_for_receiving(
            token_address=to_token_address, chain_id=to_chain_id, check_balance_on_dst=True
        )

        await self.client.send_transaction(transaction)

        self.logger_msg(*self.client.acc_info,
                        msg=f"Bridge complete. Note: wait a little for receiving funds", type_msg='success')

        return await self.client.wait_for_receiving(
            token_address=to_token_address, old_balance=old_balance_on_dst, chain_id=to_chain_id
        )
