from modules import DEX, Logger
from utils.tools import gas_checker, helper
from general_settings import SLIPPAGE
from hexbytes import HexBytes
from config import (
    UNISWAP_ABI,
    UNISWAP_CONTRACTS,
    TOKENS_PER_CHAIN
)


class Uniswap(DEX, Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)
        self.network = self.client.network.name
        self.router_contract = self.client.get_contract(
            UNISWAP_CONTRACTS[self.network]['router'],
            UNISWAP_ABI['router']
        )
        self.quoter_contract = self.client.get_contract(
            UNISWAP_CONTRACTS[self.network]['quoter'],
            UNISWAP_ABI['quoter']
        )

    def get_path(self, from_token_address: str, to_token_address: str, from_token_name: str, to_token_name: str):

        pool_fee_info = {
            'Base': {
                "USDC.e/ETH": 500,
                "ETH/USDC.e": 500,
            },
            'Polygon':{
                'USDT/MATIC': 500,
                'MATIC/USDT': 500,
                'USDC.e/MATIC': 500,
                'MATIC/USDC.e': 500,
                'USDC/MATIC': 500,
                'MATIC/USDC': 500,
                'MATIC/WETH': 500,
                'WETH/MATIC': 500,
            }
        }[self.client.network.name]

        if 'USDT' not in [from_token_name, to_token_name] or self.client.network.name == 'Polygon':
            from_token_bytes = HexBytes(from_token_address).rjust(20, b'\0')
            to_token_bytes = HexBytes(to_token_address).rjust(20, b'\0')
            fee_bytes = pool_fee_info[f"{from_token_name}/{to_token_name}"].to_bytes(3, 'big')
            return from_token_bytes + fee_bytes + to_token_bytes
        else:
            from_token_bytes = HexBytes(from_token_address).rjust(20, b'\0')
            index_1 = f'{from_token_name}/USDC'
            fee_bytes_1 = pool_fee_info[index_1].to_bytes(3, 'big')
            middle_token_bytes = HexBytes(TOKENS_PER_CHAIN[self.network]['USDC']).rjust(20, b'\0')
            index_2 = f'USDC/{to_token_name}'
            fee_bytes_2 = pool_fee_info[index_2].to_bytes(3, 'big')
            to_token_bytes = HexBytes(to_token_address).rjust(20, b'\0')
            return from_token_bytes + fee_bytes_1 + middle_token_bytes + fee_bytes_2 + to_token_bytes

    async def get_min_amount_out(self, path: bytes, amount_in_wei: int):
        min_amount_out, _, _, _ = await self.quoter_contract.functions.quoteExactInput(
            path,
            amount_in_wei
        ).call()

        return int(min_amount_out - (min_amount_out / 100 * SLIPPAGE))

    @helper
    @gas_checker
    async def swap(self, swapdata: tuple = None):
        if not swapdata:
            from_token_name, to_token_name, amount, amount_in_wei = 'MATIC', 'USDT', 1, int(1 * 10 ** 18)#await self.client.get_auto_amount()
        else:
            from_token_name, to_token_name, amount, amount_in_wei = swapdata

        self.logger_msg(
            *self.client.acc_info, msg=f'Swap on Uniswap: {amount} {from_token_name} -> {to_token_name}')

        from_token_address = TOKENS_PER_CHAIN[self.network][from_token_name]
        to_token_address = TOKENS_PER_CHAIN[self.network][to_token_name]

        path = self.get_path(from_token_address, to_token_address, from_token_name, to_token_name)
        min_amount_out = await self.get_min_amount_out(path, amount_in_wei)

        await self.client.price_impact_defender(from_token_name, amount, to_token_name, min_amount_out)

        if from_token_name != self.client.token:
            await self.client.check_for_approved(
                from_token_address, UNISWAP_CONTRACTS[self.network]['router'], amount_in_wei
            )

        tx_data = self.router_contract.encodeABI(
            fn_name='exactInput',
            args=[(
                path,
                self.client.address if to_token_name != self.client.token else '0x0000000000000000000000000000000000000002',
                amount_in_wei,
                min_amount_out
            )]
        )

        full_data = [tx_data]

        if from_token_name == self.client.token or to_token_name == self.client.token:
            tx_additional_data = self.router_contract.encodeABI(
                fn_name='unwrapWETH9' if from_token_name != self.client.token else 'refundETH',
                args=[
                    min_amount_out,
                    self.client.address
                ] if from_token_name != self.client.token else None
            )
            full_data.append(tx_additional_data)

        tx_params = await self.client.prepare_transaction(
            value=amount_in_wei if from_token_name == self.client.token else 0
        )

        transaction = await self.router_contract.functions.multicall(
            full_data
        ).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)
