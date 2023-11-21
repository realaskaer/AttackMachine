from modules import DEX
from utils.tools import gas_checker, repeater
from settings import SLIPPAGE
from config import WOOFI_ROUTER_ABI, TOKENS_PER_CHAIN, WOOFI_CONTRACTS, ETH_MASK


class WooFi(DEX):
    def __init__(self, client):
        self.client = client

        self.router_contract = self.client.get_contract(WOOFI_CONTRACTS['router'], WOOFI_ROUTER_ABI)

    async def get_min_amount_out(self, from_token_address: str, to_token_address: str, amount_in_wei: int):
        min_amount_out = await self.router_contract.functions.querySwap(
            from_token_address,
            to_token_address,
            amount_in_wei
        ).call()

        return int(min_amount_out - (min_amount_out / 100 * SLIPPAGE))

    @repeater
    @gas_checker
    async def swap(self):

        from_token_name, to_token_name, amount, amount_in_wei = await self.client.get_auto_amount()

        self.client.logger.info(
            f'{self.client.info} Swap on WooFi: {amount} {from_token_name} -> {to_token_name}')

        token_data = TOKENS_PER_CHAIN[self.client.network.name]

        from_token_address = ETH_MASK if from_token_name == "ETH" else token_data[from_token_name]
        to_token_address = ETH_MASK if to_token_name == "ETH" else token_data[to_token_name]

        if from_token_address != ETH_MASK:
            await self.client.check_for_approved(from_token_address, WOOFI_CONTRACTS['router'], amount_in_wei)

        min_amount_out = await self.get_min_amount_out(from_token_address, to_token_address, amount_in_wei)

        tx_params = await self.client.prepare_transaction(value=amount_in_wei if from_token_name == 'ETH' else 0)

        transaction = await self.router_contract.functions.swap(
            from_token_address,
            to_token_address,
            amount_in_wei,
            min_amount_out,
            self.client.address,
            self.client.address
        ).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)
