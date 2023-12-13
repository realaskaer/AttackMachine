from modules import Bridge, Logger
from utils.tools import helper, gas_checker
from config import ORBITER_CONTRACTS, ORBITER_ABI, TOKENS_PER_CHAIN
from settings import GLOBAL_NETWORK
from web3 import AsyncWeb3


class Orbiter(Bridge, Logger):
    def __init__(self, client):
        Logger.__init__(self)
        super().__init__(client)

    async def get_maker_data(self, from_chain: int, to_chain:int, token_name: str):

        url = 'https://openapi.orbiter.finance/explore/v3/yj6toqvwh1177e1sexfy0u1pxx5j8o47'

        request_data = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "orbiter_getTradingPairs",
            "params": []
        }

        response = await self.make_request(method='POST', url=url, json=request_data)

        data = response['result']['ruleList']
        bridge_data = {}

        path = f'{from_chain}-{to_chain}:{token_name}-{token_name}'

        for chain_data in data:
            if chain_data['pairId'] == path:

                bridge_data = {
                    'maker': chain_data['sender'],
                    'fee': chain_data['tradingFee'],
                    'decimals': chain_data['fromChain']['decimals'],
                    'min_amount': chain_data['fromChain']['minPrice'],
                    'max_amount': chain_data['fromChain']['maxPrice'],
                } | ({'recipient': chain_data['recipient']} if GLOBAL_NETWORK == 9 else {})

        if bridge_data:
            return bridge_data
        raise RuntimeError(f'That bridge is not active!')

    @helper
    @gas_checker
    async def bridge(self, chain_from_id:int, private_keys:dict = None):
        if GLOBAL_NETWORK == 9 and chain_from_id == 9:
            await self.client.initialize_account()
        elif GLOBAL_NETWORK == 9 and chain_from_id != 9:
            await self.client.session.close()
            self.client = await self.client.initialize_evm_client(private_keys['evm_key'], chain_from_id)

        from_chain, to_chain, amount, to_chain_id = await self.client.get_bridge_data(chain_from_id, 'Orbiter')
        token_name = 'ETH'

        bridge_info = f'{amount} {token_name} from {from_chain["name"]} to {to_chain["name"]}'
        self.logger_msg(*self.client.acc_info, msg=f'Bridge on Orbiter: {bridge_info}')

        bridge_data = await self.get_maker_data(from_chain['chainId'], to_chain['chainId'], token_name)
        destination_code = 9000 + to_chain['id']
        fee = int(float(bridge_data['fee']) * 10 ** bridge_data['decimals'])
        min_price, max_price = bridge_data['min_amount'], bridge_data['max_amount']
        amount_in_wei = int(amount * 10 ** bridge_data['decimals'])
        full_amount = amount_in_wei + destination_code + fee

        if from_chain['name'] != 'Starknet' and to_chain['name'] == 'Starknet':

            contract = self.client.get_contract(ORBITER_CONTRACTS["evm_contracts"][self.client.network.name],
                                                ORBITER_ABI['evm_contract'])

            receiver = await self.get_address_for_bridge(private_keys['stark_key'], stark_key_type=True)

            transaction = [await contract.functions.transfer(
                AsyncWeb3.to_checksum_address(bridge_data['recipient']),
                "0x03" + f'{receiver[2:]:0>64}'
            ).build_transaction(await self.client.prepare_transaction(value=full_amount))]

        elif from_chain['name'] == 'Starknet' and to_chain['name'] != 'Starknet':

            contract = await self.client.get_contract(ORBITER_CONTRACTS["stark_contract"])
            eth_address = TOKENS_PER_CHAIN['Starknet']['ETH']

            approve_call = self.client.get_approve_call(eth_address, ORBITER_CONTRACTS['stark_contract'],
                                                        unlim_approve=True)

            bridge_call = contract.functions["transferERC20"].prepare(
                eth_address,
                int(bridge_data['recipient'], 16),
                full_amount,
                int(await self.get_address_for_bridge(private_keys['evm_key'], stark_key_type=False), 16)
            )

            transaction = approve_call, bridge_call
        else:
            transaction = [(await self.client.prepare_transaction(value=full_amount)) | {
                'to': self.client.w3.to_checksum_address(bridge_data['maker'])
            }]

        if min_price <= amount <= max_price:

            balance_in_wei, _, _ = await self.client.get_token_balance(token_name)
            if balance_in_wei > full_amount:

                result = await self.client.send_transaction(*transaction)

                await self.client.wait_for_receiving(to_chain_id)

                return result

            else:
                raise RuntimeError(f'Insufficient balance!')
        else:
            raise RuntimeError(f"Limit range for bridge: {min_price} – {max_price} {token_name}!")
