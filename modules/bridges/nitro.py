from config import ETH_MASK, CHAIN_NAME_FROM_ID
from modules import Bridge, Logger, Client
from utils.tools import helper


class Nitro(Bridge, Logger):
    def __init__(self, client: Client):
        self.client = client
        Logger.__init__(self)
        Bridge.__init__(self, client)

        self.chain_ids = {
            "ethereum": "1",
            "arbitrum": "42161",
            "optimism": "10",
            "zksync": "324",
            "scroll": "534352",
            "base": "8453",
            "linea": "59144",
        }

    async def get_quote(self, to_chain_id, from_token_address, to_token_address, amount):
        url = "https://api-beta.pathfinder.routerprotocol.com/api/v2/quote"

        params = {
            "fromTokenAddress": from_token_address,
            "toTokenAddress": to_token_address,
            "amount": amount,
            "fromTokenChainId": self.client.chain_id,
            "toTokenChainId": to_chain_id,
            "partnerId": 1
        }

        return await self.make_request(url=url, params=params)

    async def build_tx(self, quote: dict):
        url = "https://api-beta.pathfinder.routerprotocol.com/api/v2/transaction"

        quote |= {
            'receiverAddress': self.client.address,
            'senderAddress': self.client.address
        }

        response = await self.make_request(method="POST", url=url, json=quote)

        return response['txn']['data'], self.client.w3.to_checksum_address(response['txn']['to'])

    @helper
    async def bridge(self, chain_from_id: int, bridge_data: tuple, need_check: bool = False):
        (from_chain, to_chain, amount, to_chain_id, from_token_name,
         to_token_name, from_token_address, to_token_address) = bridge_data

        if need_check:
            return 0

        bridge_info = f'{self.client.network.name} -> {to_token_name} {CHAIN_NAME_FROM_ID[to_chain]}'
        self.logger_msg(*self.client.acc_info, msg=f'Bridge on Nitro: {amount} {from_token_name} {bridge_info}')

        decimals = await self.client.get_decimals(token_address=from_token_address)
        amount_in_wei = self.client.to_wei(amount, decimals=decimals)

        if from_token_name == 'ETH':
            from_token_address = ETH_MASK
        if to_token_name == 'ETH':
            to_token_address = ETH_MASK

        route_data = await self.get_quote(to_chain, from_token_address, to_token_address, amount_in_wei)
        tx_data, to_address = await self.build_tx(route_data)

        if from_token_name != self.client.token:
            await self.client.check_for_approved(from_token_address, to_address, amount_in_wei)

        transaction = await self.client.prepare_transaction(value=amount_in_wei) | {
            'to': to_address,
            'data': tx_data
        }

        old_balance_on_dst = await self.client.wait_for_receiving(
            token_address=to_token_address, token_name=to_token_name, chain_id=to_chain_id, check_balance_on_dst=True
        )

        await self.client.send_transaction(transaction)

        self.logger_msg(*self.client.acc_info,
                        msg=f"Bridge complete. Note: wait a little for receiving funds", type_msg='success')

        return await self.client.wait_for_receiving(
            token_address=to_token_address, token_name=to_token_name, old_balance=old_balance_on_dst,
            chain_id=to_chain_id
        )