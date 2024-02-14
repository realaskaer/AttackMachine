from modules import Bridge, Logger
from modules.interfaces import BridgeExceptionWithoutRetry, SoftwareExceptionWithoutRetry, RequestClient
from config import CHAIN_NAME_FROM_ID
from web3 import AsyncWeb3


class Owlto(Bridge, Logger, RequestClient):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)
        Bridge.__init__(self, client)
        RequestClient.__init__(self, client)

    async def get_chains_info(self, chain_id:int, chain_name:int):

        url = 'https://owlto.finance/api/config/all-chains'

        bridge_config = (await self.make_request(url=url))['msg']

        to_chain_info = [
            {
                'name': bridge_data['name'],
                'networkCode': bridge_data['networkCode'],
            }
            for bridge_data in bridge_config
            if bridge_data['networkCode'] == chain_id or bridge_data['aliasName'] == chain_name][0]

        chain_id = self.client.network.chain_id
        chain_name = self.client.network.name

        from_chain_info = [
            {
                'name': bridge_data['name'],
            }
            for bridge_data in bridge_config
            if bridge_data['networkCode'] == chain_id or bridge_data['aliasName'] == chain_name][0]

        if from_chain_info and to_chain_info:
            return from_chain_info, to_chain_info
        raise BridgeExceptionWithoutRetry(f'That bridge is not active!')

    async def get_lp_config(self, chain_id:int, token_name:str):

        url = 'https://owlto.finance/api/lp-info'

        params = {
            'token': token_name,
            'from_chainid': self.client.network.chain_id,
            'to_chainid': chain_id,
            'user': self.client.address
        }

        lp_config = (await self.make_request(url=url, params=params))['msg']

        from_token_address = lp_config['from_token_address']
        to_token_address = lp_config['to_token_address']
        bridge_address = lp_config['bridge_contract_address']
        decimals = int(lp_config['token_decimal'])
        min_amount_in_wei, max_amount_in_wei = int(lp_config['min']), int(lp_config['max'])
        min_amount = round(min_amount_in_wei / 10 ** decimals, 6)
        max_amount = round(max_amount_in_wei / 10 ** decimals, 6)

        return (lp_config['maker_address'], min_amount, max_amount, decimals,
                bridge_address, from_token_address, to_token_address)

    async def get_tx_fee(self, from_chain_name, to_chain_name, amount, token_name):

        url = 'https://owlto.finance/api/dynamic-dtc'

        params = {
            'from': from_chain_name,
            'to': to_chain_name,
            'amount': amount,
            'token': token_name
        }

        return float((await self.make_request(url=url, params=params))['msg'])

    async def bridge(self, chain_from_id: int, bridge_data: tuple, need_check: bool = False):
        from_chain, to_chain, amount, to_chain_id, token_name, _, _ = bridge_data

        if not need_check:
            bridge_info = f'{self.client.network.name} -> {token_name} {CHAIN_NAME_FROM_ID[to_chain]}'
            self.logger_msg(*self.client.acc_info, msg=f'Bridge on Owlto: {amount} {token_name} {bridge_info}')

        from_chain_info, to_chain_info = await self.get_chains_info(from_chain, to_chain)
        lp_config = await self.get_lp_config(to_chain, token_name)
        (maker_address, min_amount, max_amount, decimals,
         bridge_contract_address, from_token_address, to_token_address) = lp_config

        fee = await self.get_tx_fee(from_chain_info['name'], to_chain_info['name'], amount, token_name)

        destination_code = int(to_chain_info['networkCode'])
        fee_in_wei = int(fee * 10 ** decimals)
        amount_in_wei = self.client.to_wei(round(amount, 6), decimals)
        full_amount = int(round(amount_in_wei + fee_in_wei, -2) + destination_code)

        if need_check:
            print(round(float(full_amount / 10 ** decimals), 6))
            return round(float(full_amount / 10 ** decimals), 6)

        if token_name != self.client.network.token:
            contract = self.client.get_contract(from_token_address)

            transaction = await contract.functions.transfer(
                AsyncWeb3.to_checksum_address(maker_address),
                full_amount
            ).build_transaction(await self.client.prepare_transaction())
        else:
            transaction = (await self.client.prepare_transaction(value=full_amount)) | {
                'to': self.client.w3.to_checksum_address(maker_address)
            }

        if min_amount <= amount <= max_amount:
            if int(f"{full_amount}"[-2:]) != destination_code:
                raise SoftwareExceptionWithoutRetry('Math problem in Python. Machine will save your money =)')

            old_balance_on_dst = await self.client.wait_for_receiving(
                token_address=from_token_address, chain_id=to_chain_id, check_balance_on_dst=True
            )

            await self.client.send_transaction(transaction)

            self.logger_msg(*self.client.acc_info,
                            msg=f"Bridge complete. Note: wait a little for receiving funds", type_msg='success')

            return await self.client.wait_for_receiving(
                token_address=from_token_address, old_balance=old_balance_on_dst, chain_id=to_chain_id
            )

        else:
            raise BridgeExceptionWithoutRetry(f"Limit range for bridge: {min_amount} – {max_amount} {token_name}!")
