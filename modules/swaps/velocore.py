from eth_abi import abi
from eth_utils import to_bytes, to_hex
from modules import DEX, Logger, Client
from utils.tools import gas_checker, helper
from general_settings import SLIPPAGE
from config import (
    VELOCORE_CONTRACTS,
    VELOCORE_ABI,
    TOKENS_PER_CHAIN
)


class Velocore(DEX, Logger):
    def __init__(self, client: Client):
        self.client = client
        Logger.__init__(self)
        self.network = self.client.network.name
        self.router_contract = self.client.get_contract(
            VELOCORE_CONTRACTS[self.network]['router'], VELOCORE_ABI['router'])
        self.multicall_contract = self.client.get_contract(
            VELOCORE_CONTRACTS[self.network]['multicall'], VELOCORE_ABI['multicall'])

    @staticmethod
    def to_token_info(token_ref_index: int, method: int, min_amount_out:int = 0) -> str:
        encode_amount = 2 ** 127 - 1 - min_amount_out
        return to_bytes(token_ref_index) + to_bytes(method) + abi.encode(['uint128'], [encode_amount])[2:]

    async def get_min_amount_out(
            self, from_token_address:str, to_token_address:str, reverse_flag: bool, pool_address, amounts: list
    ):
        at_most = 1
        _all = 2
        eth_mask = '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee'

        data = await self.multicall_contract.functions.aggregate3(
            [
                (
                    self.router_contract.address,
                    True,
                    to_bytes(hexstr=self.router_contract.encodeABI(
                        fn_name='query',
                        args=(
                            self.client.address,
                            [
                                abi.encode(['address'], [to_token_address if reverse_flag else from_token_address]),
                                eth_mask,
                            ],
                            amounts,
                            [
                                [
                                    abi.encode(['address'], [pool_address]),
                                    [
                                        self.to_token_info(0x00, at_most if reverse_flag else _all),
                                        self.to_token_info(0x01, _all if reverse_flag else at_most),
                                    ],
                                    '0x00'
                                ]
                            ]
                        )
                    )
                    )
                )
            ]
        ).call()
        hex_data = to_hex(data[0][1])
        token_amount_hex = hex_data[-128:-64] if reverse_flag else hex_data[-64:]

        min_amount_out = int(token_amount_hex, 16)

        return int(min_amount_out - (min_amount_out / 100 * SLIPPAGE))

    @helper
    @gas_checker
    async def swap(self):
        from_token_name, to_token_name, amount, amount_in_wei = await self.client.get_auto_amount()

        self.logger_msg(*self.client.acc_info, msg=f'Swap on Velocore: {amount} {from_token_name} -> {to_token_name}')

        eth_mask = '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee'
        from_token_address = TOKENS_PER_CHAIN[self.network][from_token_name] if from_token_name != 'ETH' else eth_mask
        to_token_address = TOKENS_PER_CHAIN[self.network][to_token_name] if to_token_name != 'ETH' else eth_mask

        at_most = 1
        _all = 2
        to_index_id = 0x01 if from_token_name != 'ETH' else 0x00
        reverse_flag = True if from_token_address == eth_mask else False
        amounts = [0, amount_in_wei] if reverse_flag else [amount_in_wei, 0]
        pool_address = {
            'zkSync':{
                'USDC/ETH': '0x42D106c4A1d0Bc5C482c11853A3868d807A3781d',
                'ETH/USDC': '0x42D106c4A1d0Bc5C482c11853A3868d807A3781d',
                'USDT/ETH': '0xF0e86a60Ae7e9bC0F1e59cAf3CC56f434b3024c0',
                'ETH/USDT': '0xF0e86a60Ae7e9bC0F1e59cAf3CC56f434b3024c0',
            },
            'Linea':{
                'USDC/ETH': '0xe2c67A9B15e9E7FF8A9Cb0dFb8feE5609923E5DB',
                'ETH/USDC': '0xe2c67A9B15e9E7FF8A9Cb0dFb8feE5609923E5DB',
                'USDT/ETH': '0x820AaFf56fa2F6Ea552e86B7C2Da541d67195d07',
                'ETH/USDT': '0x820AaFf56fa2F6Ea552e86B7C2Da541d67195d07',
            }
        }[self.client.network.name][f'{from_token_name}/{to_token_name}']

        min_amount_out = await self.get_min_amount_out(
            from_token_address, to_token_address, reverse_flag, pool_address, amounts
        )

        await self.client.price_impact_defender(from_token_name, amount, to_token_name, min_amount_out)

        if from_token_name != 'ETH':
            await self.client.check_for_approved(
                from_token_address, VELOCORE_CONTRACTS[self.network]['router'], amount_in_wei
            )

        tx_params = await self.client.prepare_transaction(value=amount_in_wei if from_token_name == 'ETH' else 0)
        transaction = await self.router_contract.functions.execute(
            [
                abi.encode(['address'], [to_token_address if reverse_flag else from_token_address]),
                eth_mask,
            ],
            [
                amount_in_wei if from_token_name != 'ETH' else 0,
                0
            ],
            [
                [
                    abi.encode(['address'], [pool_address]),
                    [
                        self.to_token_info(0x00, at_most if reverse_flag else _all),
                        self.to_token_info(0x01, _all if reverse_flag else at_most),
                    ],
                    '0x00'
                ],
                [
                    "0x0500000000000000000000000000000000000000000000000000000000000000",
                    [
                        self.to_token_info(to_index_id, at_most, min_amount_out),
                    ],
                    '0x00'
                ]
            ]
        ).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)
