from modules import Client
from utils.tools import gas_checker, repeater
from settings import SLIPPAGE_PERCENT
from config import WOOFI_ROUTER_ABI, ZKSYNC_TOKENS, WOOFI_CONTRACTS, ETH_MASK


class WooFi(Client):
    def __init__(self, account_number, private_key, network, proxy=None):
        super().__init__(account_number, private_key, network, proxy)
        self.router_contract = self.get_contract(WOOFI_CONTRACTS['router'], WOOFI_ROUTER_ABI)

    async def get_min_amount_out(self, from_token_address: str, to_token_address: str, amount_in_wei: int):
        min_amount_out = await self.router_contract.functions.querySwap(
            from_token_address,
            to_token_address,
            amount_in_wei
        ).call()

        return int(min_amount_out - (min_amount_out / 100 * SLIPPAGE_PERCENT))

    @repeater
    @gas_checker
    async def swap(self):

        from_token_name, to_token_name, amount, amount_in_wei = await self.get_auto_amount()

        self.logger.info(f'{self.info} Swap on WooFi: {amount} {from_token_name} -> {to_token_name}')

        from_token_address = ETH_MASK if from_token_name == "ETH" else ZKSYNC_TOKENS[from_token_name]
        to_token_address = ETH_MASK if to_token_name == "ETH" else ZKSYNC_TOKENS[to_token_name]

        if from_token_address != ETH_MASK:
            await self.check_for_approved(from_token_address, WOOFI_CONTRACTS['router'], amount_in_wei)

        min_amount_out = await self.get_min_amount_out(from_token_address, to_token_address, amount_in_wei)

        tx_params = await self.prepare_transaction(value=amount_in_wei if from_token_name == 'ETH' else 0)

        transaction = await self.router_contract.functions.swap(
            from_token_address,
            to_token_address,
            amount_in_wei,
            min_amount_out,
            self.address,
            self.address
        ).build_transaction(tx_params)

        tx_hash = await self.send_transaction(transaction)

        await self.verify_transaction(tx_hash)
