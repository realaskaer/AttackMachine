from modules import Bridge, Logger
from modules.interfaces import BridgeExceptionWithoutRetry
from config import TOKENS_PER_CHAIN, ACROSS_ABI, CHAIN_NAME_FROM_ID, ACROSS_CONTRACT
from general_settings import GAS_LIMIT_MULTIPLIER


class Across(Bridge, Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)
        Bridge.__init__(self, client)
        self.network = self.client.network.name

    async def get_bridge_fee(self, chain_id, amount_in_wei, token_address):
        url = 'https://across.to/api/suggested-fees'

        params = {
            'token': token_address,
            'destinationChainId': chain_id,
            'amount': amount_in_wei,
            'originChainId': self.client.chain_id
        }

        fees_data = await self.make_request(url=url, params=params)

        return (fees_data['spokePoolAddress'], int(fees_data['relayFeePct']),
                int(fees_data['relayGasFeeTotal']), int(fees_data['timestamp']))

    async def get_bridge_limits(self, chain_id, token_address):
        url = 'https://across.to/api/limits'

        params = {
            'token': token_address,
            'destinationChainId': chain_id,
            'originChainId': self.client.chain_id
        }

        limits_data = await self.make_request(url=url, params=params)

        return int(limits_data['minDeposit']), int(limits_data['maxDeposit'])

    async def check_available_routes(self, chain_id, token_name):
        url = 'https://across.to/api/available-routes'

        params = {
            'originChainId': self.client.chain_id,
            'destinationChainId': chain_id,
            'originToken': TOKENS_PER_CHAIN[self.network][token_name],
            'destinationToken': TOKENS_PER_CHAIN[CHAIN_NAME_FROM_ID[chain_id]][token_name],
        }

        return await self.make_request(url=url, params=params)

    async def bridge(self, chain_from_id: int, bridge_data: tuple, need_check: bool = False):
        from_chain, to_chain, amount, to_chain_id, token_name, _, from_token_address, to_token_address = bridge_data

        if not need_check:
            bridge_info = f'{self.client.network.name} -> {token_name} {CHAIN_NAME_FROM_ID[to_chain]}'
            self.logger_msg(*self.client.acc_info, msg=f'Bridge on Across: {amount} {token_name} {bridge_info}')

        amount_in_wei = self.client.to_wei(amount)

        min_limit, max_limit = await self.get_bridge_limits(to_chain, from_token_address)

        if min_limit <= amount_in_wei <= max_limit:

            if await self.check_available_routes(to_chain, token_name):

                pool_adress, relay_fee_pct, relay_gas_fee_total, timestamp = await self.get_bridge_fee(
                    to_chain, amount_in_wei, from_token_address
                )

                if need_check:
                    return round(float(relay_gas_fee_total / 10 ** 18), 6)

                data = [
                    self.client.address,
                    from_token_address,
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
                    router_contract = self.client.get_contract(
                        contract_address=ACROSS_CONTRACT[self.network], abi=ACROSS_ABI['router']
                    )

                if token_name != self.client.token:
                    value = 0
                else:
                    value = amount_in_wei

                transaction = await router_contract.functions.deposit(
                    *data
                ).build_transaction(await self.client.prepare_transaction(value=value))

                transaction['data'] += 'd00dfeeddeadbeef000000a679c2fb345ddefbae3c42bee92c0fb7a5'
                transaction['gas'] = int(transaction['gas'] * GAS_LIMIT_MULTIPLIER)

                old_balance_on_dst = await self.client.wait_for_receiving(
                    token_address=to_token_address, chain_id=to_chain_id, check_balance_on_dst=True
                )

                await self.client.send_transaction(transaction)

                self.logger_msg(*self.client.acc_info,
                                msg=f"Bridge complete. Note: wait a little for receiving funds", type_msg='success')

                return await self.client.wait_for_receiving(
                    token_address=to_token_address, old_balance=old_balance_on_dst, chain_id=to_chain_id
                )

            else:
                raise BridgeExceptionWithoutRetry(f'Bridge route is not available!')
        else:
            min_limit, max_limit = min_limit / 10 ** 18, max_limit / 10 ** 18
            raise BridgeExceptionWithoutRetry(f'Limit range for bridge: {min_limit:.5f} - {max_limit:.2f} ETH!')
