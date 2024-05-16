from modules import Bridge, Logger
from modules.interfaces import BridgeExceptionWithoutRetry
from config import TOKENS_PER_CHAIN, ACROSS_ABI, CHAIN_NAME_FROM_ID, ACROSS_CONTRACT, ACROSS_CLAIM_CONTRACTS
from general_settings import GAS_LIMIT_MULTIPLIER
from settings import WAIT_FOR_RECEIPT_BRIDGE
from utils.tools import helper, gas_checker


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

    async def check_available_routes(self, chain_id, from_token_address, to_token_address):
        url = 'https://across.to/api/available-routes'

        params = {
            'originChainId': self.client.chain_id,
            'destinationChainId': chain_id,
            'originToken': from_token_address,
            'destinationToken': to_token_address,
        }

        return await self.make_request(url=url, params=params)

    async def bridge(self, chain_from_id: int, bridge_data: tuple, need_check: bool = False):
        (from_chain, to_chain, amount, to_chain_id, from_token_name,
         to_token_name, from_token_address, to_token_address) = bridge_data

        if not need_check:
            bridge_info = f'{self.client.network.name} -> {from_token_name} {CHAIN_NAME_FROM_ID[to_chain]}'
            self.logger_msg(*self.client.acc_info, msg=f'Bridge on Across: {amount} {from_token_name} {bridge_info}')

        decimals = await self.client.get_decimals(token_address=from_token_address)
        amount_in_wei = self.client.to_wei(amount, decimals)

        min_limit, max_limit = await self.get_bridge_limits(to_chain, from_token_address)

        if min_limit <= amount_in_wei <= max_limit:

            if await self.check_available_routes(to_chain, from_token_address, to_token_address):

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

                if from_chain in [324, 137, 59144]:
                    router_contract = self.client.get_contract(contract_address=pool_adress, abi=ACROSS_ABI['pool'])
                else:
                    data.insert(0, pool_adress)
                    router_contract = self.client.get_contract(
                        contract_address=ACROSS_CONTRACT[self.network], abi=ACROSS_ABI['router']
                    )

                if from_token_name != self.client.token:
                    value = 0
                    await self.client.check_for_approved(
                        TOKENS_PER_CHAIN[self.client.network.name][from_token_name], router_contract.address,
                        amount_in_wei
                    )

                else:
                    value = amount_in_wei

                transaction = await router_contract.functions.deposit(
                    *data
                ).build_transaction(await self.client.prepare_transaction(value=value))

                transaction['data'] += 'd00dfeeddeadbeef000000a679c2fb345ddefbae3c42bee92c0fb7a5'
                transaction['gas'] = int(transaction['gas'] * GAS_LIMIT_MULTIPLIER)

                old_balance_on_dst = await self.client.wait_for_receiving(
                    token_address=to_token_address, token_name=to_token_name, chain_id=to_chain_id,
                    check_balance_on_dst=True
                )

                await self.client.send_transaction(transaction)

                self.logger_msg(
                    *self.client.acc_info, msg=f"Bridge complete. Note: wait a little for receiving funds",
                    type_msg='success'
                )

                if WAIT_FOR_RECEIPT_BRIDGE:
                    return await self.client.wait_for_receiving(
                        token_address=to_token_address, token_name=to_token_name, old_balance=old_balance_on_dst,
                        chain_id=to_chain_id
                    )
                return True

            else:
                raise BridgeExceptionWithoutRetry(f'Bridge route is not available!')
        else:
            min_limit, max_limit = min_limit / 10 ** decimals, max_limit / 10 ** decimals
            raise BridgeExceptionWithoutRetry(
                f'Limit range for bridge: {min_limit:.5f} - {max_limit:.2f} {from_token_name}!'
            )

    @helper
    @gas_checker
    async def claim_rewards(self):
        # url = 'https://public.api.across.to/rewards/op-rebates/summary'
        #
        # params = {
        #     'userAddress': self.client.address
        # }
        #
        # response = await self.make_request(url=url, params=params)
        #
        # if int(response['claimableRewards']) == 0:
        #     self.logger_msg(*self.client.acc_info, msg=f'No tokens are available for claiming', type_msg='warning')
        #     return True

        url = 'https://public.api.across.to/airdrop/merkle-distributor-proofs'

        params = {
            'address': self.client.address,
            'startWindowIndex': 0,
            'rewardsType': 'op-rewards',
        }

        response = await self.make_request(url=url, params=params)

        if response:
            response = response[0]

            claim_contract = self.client.get_contract(ACROSS_CLAIM_CONTRACTS[self.network], ACROSS_ABI['claim'])

            amount_in_wei = int(response['payload']['amountBreakdown']['opRewards'])

            amount = amount_in_wei / 10 ** 18

            self.logger_msg(*self.client.acc_info, msg=f'Available to claim {amount:.2f} $OP on Optimism chain')

            merkle_proof = response['proof']
            account_index = int(response['accountIndex'])
            window_index = int(response['windowIndex'])

            self.logger_msg(*self.client.acc_info, msg=f'Start claiming {amount:.2f} $OP on Optimism chain')

            transaction = await claim_contract.functions.claimMulti(
                [
                    [
                        window_index,
                        amount_in_wei,
                        account_index,
                        self.client.address,
                        merkle_proof
                    ]
                ]
            ).build_transaction(await self.client.prepare_transaction())

            return await self.client.send_transaction(transaction)

        self.logger_msg(*self.client.acc_info, msg=f'No available tokens for claiming', type_msg='warning')
        return True