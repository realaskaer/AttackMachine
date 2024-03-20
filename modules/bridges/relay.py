from config import CHAIN_NAME_FROM_ID, ZERO_ADDRESS
from modules import Bridge, Logger
from modules.interfaces import SoftwareException, SoftwareExceptionWithoutRetry


class Relay(Bridge, Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)
        Bridge.__init__(self, client)

    async def get_bridge_config(self, dest_chain_id):
        url = "https://api.relay.link/config"

        headers = {
            "accept": "*/*",
            "accept-language": "ru,en;q=0.9,en-GB;q=0.8,en-US;q=0.7",
            "sec-ch-ua": "\"Chromium\";v=\"122\", \"Not(A:Brand\";v=\"24\", \"Microsoft Edge\";v=\"122\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "referrer": "https://www.relay.link/",
            "referrerPolicy": "strict-origin-when-cross-origin",
        }

        params = {
            'originChainId': self.client.network.chain_id,
            'destinationChainId': dest_chain_id,
            'user': ZERO_ADDRESS,
            'currency': ZERO_ADDRESS,
        }

        return await self.make_request(url=url, headers=headers, params=params)

    async def get_bridge_data(self, dest_chain_id, amount_in_wei):
        url = f"https://api.relay.link/execute/call"

        payload = {
            "user": self.client.address,
            "txs": [
                {
                    "to": self.client.address,
                    "value": amount_in_wei,
                    "data": "0x"
                }
            ],
            "originChainId": self.client.network.chain_id,
            "destinationChainId": dest_chain_id,
            "source": "relay.link"
        }

        return await self.make_request(method='POST', url=url, json=payload)

    async def bridge(self, chain_from_id: int, bridge_data: tuple, need_check: bool = False):
        from_chain, to_chain, amount, to_chain_id, token_name, _, from_token_address, to_token_address = bridge_data

        supported_chains = [42161, 42170, 8453, 10, 324, 1, 7777777]
        if from_chain not in supported_chains or to_chain not in supported_chains:
            raise SoftwareExceptionWithoutRetry(
                f'Bridge from {self.client.network.name} to {CHAIN_NAME_FROM_ID[to_chain]} is not exist')

        if not need_check:
            bridge_info = f'{self.client.network.name} -> {token_name} {CHAIN_NAME_FROM_ID[to_chain]}'
            self.logger_msg(*self.client.acc_info, msg=f'Bridge on Relay: {amount} {token_name} {bridge_info}')

        decimals = 18 if token_name == self.client.token else await self.client.get_decimals(
            token_address=from_token_address
        )

        amount_in_wei = self.client.to_wei(amount, decimals)
        networks_data = await self.get_bridge_config(to_chain)
        tx_data = await self.get_bridge_data(dest_chain_id=to_chain, amount_in_wei=amount_in_wei)

        if need_check:
            fee = int(int(tx_data['fees']['gas']) * 1.2)
            return round(float(fee / 10 ** decimals), 6)

        if networks_data['enabled']:

            max_amount = networks_data['solver']['capacityPerRequest']

            if amount <= float(max_amount):

                transaction = (await self.client.prepare_transaction(value=amount_in_wei)) | {
                    'to': self.client.w3.to_checksum_address(tx_data["steps"][0]['items'][0]['data']['to']),
                    'data': tx_data["steps"][0]['items'][0]['data']['data']
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
            else:
                raise SoftwareException(f"Limit range for bridge: 0 - {max_amount} ETH")
        else:
            raise SoftwareException(
                f"Bridge from {self.client.network.name} -> {CHAIN_NAME_FROM_ID[to_chain]} is not active!")
