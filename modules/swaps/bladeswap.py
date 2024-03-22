from eth_abi import abi
from eth_utils import to_bytes, to_hex
from modules import DEX, Logger, Client
from utils.tools import gas_checker, helper
from general_settings import SLIPPAGE
from config import (
    BLADESWAP_CONTRACTS,
    BLADESWAP_ABI,
    TOKENS_PER_CHAIN, ETH_MASK
)


class BladeSwap(DEX, Logger):
    def __init__(self, client: Client):
        self.client = client
        Logger.__init__(self)
        self.network = self.client.network.name
        self.router_contract = self.client.get_contract(
            BLADESWAP_CONTRACTS[self.network]['router'], BLADESWAP_ABI['router'])
        self.multicall_contract = self.client.get_contract(
            BLADESWAP_CONTRACTS[self.network]['multicall'], BLADESWAP_ABI['multicall'])

    @staticmethod
    def to_token_info(token_ref_index: int, method: int, min_amount_out:int = 0) -> str:
        encode_amount = 2 ** 127 - 1 - min_amount_out
        return to_bytes(token_ref_index) + to_bytes(method) + abi.encode(['uint128'], [encode_amount])[2:]

    async def get_min_amount_out(self, reverse_flag: bool, amounts: list):
        at_most = 1
        _all = 2

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
                                abi.encode(['address'], [TOKENS_PER_CHAIN[self.network]['USDB']]),
                                abi.encode(['address'], [ETH_MASK]),
                            ],
                            amounts,
                            [
                                [
                                    abi.encode(['address'], [BLADESWAP_CONTRACTS[self.network]['weth_usdb_pool']]),
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
    async def swap(self, swapdata: tuple = None, help_deposit: bool = False):
        if swapdata:
            from_token_name, to_token_name, amount, amount_in_wei = swapdata
        else:
            from_token_name, to_token_name, amount, amount_in_wei = await self.client.get_auto_amount()

        self.logger_msg(*self.client.acc_info, msg=f'Swap on BladeSwap: {amount} {from_token_name} -> {to_token_name}')

        from_token_address = TOKENS_PER_CHAIN[self.network][from_token_name] if from_token_name != 'ETH' else ETH_MASK
        to_token_address = TOKENS_PER_CHAIN[self.network][to_token_name] if to_token_name != 'ETH' else ETH_MASK

        at_most = 1
        _all = 2
        to_index_id = 0x01 if from_token_name != 'ETH' else 0x00
        reverse_flag = True if from_token_address == ETH_MASK else False
        amounts = [0, amount_in_wei] if reverse_flag else [amount_in_wei, 0]
        min_amount_out = await self.get_min_amount_out(reverse_flag, amounts)

        await self.client.price_impact_defender(from_token_name, amount, to_token_name, min_amount_out)

        if from_token_name != 'ETH':
            await self.client.check_for_approved(
                from_token_address, BLADESWAP_CONTRACTS[self.network]['router'], amount_in_wei
            )

        tx_params = await self.client.prepare_transaction(value=amount_in_wei if from_token_name == 'ETH' else 0)
        transaction = await self.router_contract.functions.execute(
            [
                abi.encode(['address'], [from_token_address]),
                abi.encode(['address'], [to_token_address]),
            ],
            [
                amount_in_wei,
                0
            ],
            [
                [
                    abi.encode(['address'], [BLADESWAP_CONTRACTS[self.network]['weth_usdb_pool']]),
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
