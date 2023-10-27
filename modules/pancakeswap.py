from modules import Client
from utils.tools import gas_checker, repeater
from settings import SLIPPAGE_PERCENT
from hexbytes import HexBytes
from config import (
    PANCAKE_ROUTER_ABI,
    PANCAKE_QUOTER_ABI,
    PANCAKE_CONTRACTS,
    ZKSYNC_TOKENS
)


class PancakeSwap(Client):
    def __init__(self, account_number, private_key, network, proxy=None):
        super().__init__(account_number, private_key, network, proxy)
        self.router_contract = self.get_contract(PANCAKE_CONTRACTS['router'], PANCAKE_ROUTER_ABI)
        self.quoter_contract = self.get_contract(PANCAKE_CONTRACTS['quoter'], PANCAKE_QUOTER_ABI)

    @staticmethod
    def get_path(from_token_address: str, to_token_address: str):
        from_token_bytes = HexBytes(from_token_address).rjust(20, b'\0')
        to_token_bytes = HexBytes(to_token_address).rjust(20, b'\0')
        fee_bytes = (500).to_bytes(3, 'big')

        return from_token_bytes + fee_bytes + to_token_bytes

    async def get_min_amount_out(self, from_token_address: str, to_token_address: str, amount_in_wei: int):
        min_amount_out, _, _, _ = await self.quoter_contract.functions.quoteExactInputSingle([
            from_token_address,
            to_token_address,
            amount_in_wei,
            500,
            0
        ]).call()

        return int(min_amount_out - (min_amount_out / 100 * SLIPPAGE_PERCENT))

    @repeater
    @gas_checker
    async def swap(self):

        from_token_name, to_token_name, amount, amount_in_wei = await self.get_auto_amount()

        self.logger.info(f'{self.info} Swap on PancakeSwap: {amount} {from_token_name} -> {to_token_name}')

        from_token_address, to_token_address = ZKSYNC_TOKENS[from_token_name], ZKSYNC_TOKENS[to_token_name]

        if from_token_name != 'ETH':
            await self.check_for_approved(from_token_address, PANCAKE_CONTRACTS['router'], amount_in_wei)

        tx_params = await self.prepare_transaction(value=amount_in_wei if from_token_name == 'ETH' else 0)
        min_amount_out = await self.get_min_amount_out(from_token_address, to_token_address, amount_in_wei)
        path = self.get_path(from_token_address, to_token_address)

        tx_data = self.router_contract.encodeABI(
            fn_name='exactInput',
            args=[(
                path,
                self.address if to_token_name != 'ETH' else '0x0000000000000000000000000000000000000002',
                amount_in_wei,
                min_amount_out
            )]
        )

        full_data = [tx_data]

        if from_token_name == 'ETH' or to_token_name == 'ETH':
            tx_additional_data = self.router_contract.encodeABI(
                fn_name='unwrapWETH9' if from_token_name != 'ETH' else 'refundETH',
                args=[
                    min_amount_out,
                    self.address
                ] if from_token_name != 'ETH' else None
            )
            full_data.append(tx_additional_data)

        transaction = await self.router_contract.functions.multicall(
            full_data
        ).build_transaction(tx_params)

        tx_hash = await self.send_transaction(transaction)

        await self.verify_transaction(tx_hash)
