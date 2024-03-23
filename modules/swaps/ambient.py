from eth_abi import abi

from modules import DEX, Logger, Client
from utils.tools import gas_checker, helper
from general_settings import SLIPPAGE
from config import (
    AMBIENT_CONTRACT,
    AMBIENT_ABI,
    TOKENS_PER_CHAIN, ZERO_ADDRESS, COINGECKO_TOKEN_API_NAMES
)


class Ambient(DEX, Logger):
    def __init__(self, client: Client):
        self.client = client
        Logger.__init__(self)
        self.network = self.client.network.name
        self.router_contract = self.client.get_contract(AMBIENT_CONTRACT[self.network]['router'], AMBIENT_ABI['router'])

    async def get_min_amount_out(self, from_token_name, to_token_name, from_token_amount):

        api_names = COINGECKO_TOKEN_API_NAMES
        amount_in_usd = (await self.client.get_token_price(api_names[from_token_name])) * from_token_amount
        min_amount_out = (amount_in_usd / await self.client.get_token_price(api_names[to_token_name]))

        decimals = 18 if to_token_name == 'ETH' else await self.client.get_decimals(to_token_name)

        min_amount_out_in_wei = self.client.to_wei(min_amount_out, decimals)

        return int(min_amount_out_in_wei - (min_amount_out_in_wei / 100 * SLIPPAGE))

    @helper
    @gas_checker
    async def swap(self, swapdata: tuple = None, help_deposit: bool = False):
        if swapdata:
            from_token_name, to_token_name, amount, amount_in_wei = swapdata
        else:
            from_token_name, to_token_name, amount, amount_in_wei = await self.client.get_auto_amount()

        self.logger_msg(*self.client.acc_info, msg=f'Swap on Ambient: {amount} {from_token_name} -> {to_token_name}')

        tokens_data = TOKENS_PER_CHAIN[self.network]

        from_token_address = tokens_data[from_token_name]
        to_token_address = tokens_data[to_token_name]
        max_sqrt_price = 21267430153580247136652501917186561137
        min_sqrt_price = 65537
        pool_idx = 420
        reserve_flags = 0
        tip = 0

        min_amount_out = await self.get_min_amount_out(from_token_name, to_token_name, amount)

        if from_token_name != 'ETH':
            await self.client.check_for_approved(
                from_token_address, AMBIENT_CONTRACT[self.network]['router'], amount_in_wei
            )

        tx_params = await self.client.prepare_transaction(value=amount_in_wei if from_token_name == 'ETH' else 0)

        await self.client.price_impact_defender(from_token_name, amount, to_token_name, min_amount_out)

        encode_data = abi.encode(
            ['address', 'address', 'uint16', 'bool', 'bool', 'uint256', 'uint8', 'uint256', 'uint256', 'uint8'], [
                ZERO_ADDRESS,
                to_token_address if from_token_name == 'ETH' else from_token_address,
                pool_idx,
                True if from_token_name == 'ETH' else False,
                True if from_token_name == 'ETH' else False,
                amount_in_wei,
                tip,
                max_sqrt_price if from_token_name == 'ETH' else min_sqrt_price,
                min_amount_out,
                reserve_flags
            ]
        )

        transaction = await self.router_contract.functions.userCmd(
            1,
            encode_data
        ).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)
