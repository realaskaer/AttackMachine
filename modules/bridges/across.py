from modules import Bridge, Logger
from utils.tools import helper, gas_checker
from config import TOKENS_PER_CHAIN, ACROSS_ABI, CHAIN_NAME_FROM_ID, ACROSS_CONTRACT
from general_settings import GLOBAL_NETWORK, GAS_MULTIPLIER


class Across(Bridge, Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)
        Bridge.__init__(self, client)
        self.network = self.client.network.name

    async def get_bridge_fee(self, chain_id, amount_in_wei):
        url = 'https://across.to/api/suggested-fees'

        params = {
            'token': TOKENS_PER_CHAIN[self.network]['ETH'],
            'destinationChainId': chain_id,
            'amount': amount_in_wei,
            'originChainId': self.client.chain_id
        }

        fees_data = await self.make_request(url=url, params=params)

        return fees_data['spokePoolAddress'], int(fees_data['relayFeePct']), int(fees_data['timestamp'])

    async def get_bridge_limits(self, chain_id):
        url = 'https://across.to/api/limits'

        params = {
            'token': TOKENS_PER_CHAIN[self.network]['WETH'],
            'destinationChainId': chain_id,
            'originChainId': self.client.chain_id
        }

        limits_data = await self.make_request(url=url, params=params)

        return int(limits_data['minDeposit']), int(limits_data['maxDeposit'])

    async def check_available_routes(self, chain_id):
        url = 'https://across.to/api/available-routes'

        params = {
            'originChainId': self.client.chain_id,
            'destinationChainId': chain_id,
            'originToken': TOKENS_PER_CHAIN[self.network]['WETH'],
            'destinationToken': TOKENS_PER_CHAIN[CHAIN_NAME_FROM_ID[chain_id]]['WETH'],
        }

        return await self.make_request(url=url, params=params)

    @helper
    @gas_checker
    async def bridge(self, chain_from_id:int, private_keys:dict = None):
        if GLOBAL_NETWORK == 9 and chain_from_id == 9:
            await self.client.initialize_account()
        elif GLOBAL_NETWORK == 9 and chain_from_id != 9:
            await self.client.session.close()
            self.client = await self.client.initialize_evm_client(private_keys['evm_key'], chain_from_id)

        from_chain, to_chain, amount, to_chain_id = await self.client.get_bridge_data(chain_from_id, 'Across')

        bridge_info = f'{self.client.network.name} -> ETH {CHAIN_NAME_FROM_ID[to_chain]}'
        self.logger_msg(*self.client.acc_info, msg=f'Bridge on Across: {amount} ETH {bridge_info}')

        amount_in_wei = int(amount * 10 ** 18)

        min_limit, max_limit = await self.get_bridge_limits(to_chain)

        if min_limit <= amount_in_wei <= max_limit:

            if await self.check_available_routes(to_chain):

                pool_adress, relay_fee_pct, timestamp = await self.get_bridge_fee(to_chain, amount_in_wei)

                data = [
                    self.client.address,
                    TOKENS_PER_CHAIN[self.network]['WETH'],
                    amount_in_wei,
                    to_chain,
                    relay_fee_pct,
                    timestamp,
                    "0x",
                    2**256-1
                ]
                if from_chain == 324:
                    router_contract = self.client.get_contract(contract_address=pool_adress, abi=ACROSS_ABI['pool'])
                else:
                    data.insert(0, pool_adress)
                    router_contract = self.client.get_contract(contract_address=ACROSS_CONTRACT[self.network],
                                                               abi=ACROSS_ABI['router'])

                transaction = await router_contract.functions.deposit(
                    *data
                ).build_transaction(await self.client.prepare_transaction(value=amount_in_wei))

                transaction['data'] += 'd00dfeeddeadbeef000000a679c2fb345ddefbae3c42bee92c0fb7a5'
                transaction['gas'] = int(transaction['gas'] * GAS_MULTIPLIER)

                old_balance_on_dst = await self.client.wait_for_receiving(to_chain_id, check_balance_on_dst=True)

                result = await self.client.send_transaction(transaction, without_gas=True)

                self.logger_msg(*self.client.acc_info,
                                msg=f"Bridge complete. Note: wait a little for receiving funds", type_msg='success')

                await self.client.wait_for_receiving(to_chain_id, old_balance_on_dst)

                return result

            else:
                raise RuntimeError(f'Bridge route is not available!')
        else:
            min_limit, max_limit = min_limit / 10 ** 18, max_limit / 10 ** 18
            raise RuntimeError(f'Limit range for bridge: {min_limit:.5f} - {max_limit:.2f} ETH!')
