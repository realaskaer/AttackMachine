import json
from time import time
from eth_abi import abi
from general_settings import SLIPPAGE
from modules import DEX, Logger, Client
from settings import ZKSYNC_PAYMASTER_TOKEN
from utils.tools import gas_checker, helper
from modules.interfaces import SoftwareException
from eth_account.messages import encode_typed_data
from config import (
    SYNCSWAP_CONTRACTS,
    SYNCSWAP_ABI,
    ZERO_ADDRESS,
    TOKENS_PER_CHAIN
)


class SyncSwap(DEX, Logger):
    def __init__(self, client: Client):
        self.client = client
        Logger.__init__(self)
        self.network = self.client.network.name
        self.router_contract = self.client.get_contract(
            SYNCSWAP_CONTRACTS[self.network]['router'],
            SYNCSWAP_ABI['router']
        )
        self.pool_factory_contract = self.client.get_contract(
            SYNCSWAP_CONTRACTS[self.network]['classic_pool_factory'],
            SYNCSWAP_ABI['classic_pool_factory']
        )
        self.paymaster_contract = self.client.get_contract(
            SYNCSWAP_CONTRACTS[self.network]['paymaster'],
            SYNCSWAP_ABI['paymaster']
        )

    async def get_swap_permit(self, token_name:str):
        token_name_for_permit, version = {
            'USDT': ("Tether USD", 1),
            'USDC': ("USD Coin" if self.client.network.name == "Scroll" else 'USDC', 2)
        }[token_name]

        deadline = int(time()) + 10800

        permit_data = {
            "types": {
                "Permit": [
                    {
                        "name": "owner",
                        "type": "address"
                    },
                    {
                        "name": "spender",
                        "type": "address"
                    },
                    {
                        "name": "value",
                        "type": "uint256"
                    },
                    {
                        "name": "nonce",
                        "type": "uint256"
                    },
                    {
                        "name": "deadline",
                        "type": "uint256"
                    }
                ],
                "EIP712Domain": [
                    {
                        "name": "name",
                        "type": "string"
                    },
                    {
                        "name": "version",
                        "type": "string"
                    },
                    {
                        "name": "chainId",
                        "type": "uint256"
                    },
                    {
                        "name": "verifyingContract",
                        "type": "address"
                    }
                ]
            },
            "domain": {
                "name": token_name_for_permit,
                "version": f"{version}",
                "chainId": self.client.chain_id,
                "verifyingContract": TOKENS_PER_CHAIN[self.client.network.name][token_name]
            },
            "primaryType": "Permit",
            "message": {
                "owner": self.client.address,
                "spender": self.router_contract.address,
                "value": 2 ** 256 - 1,
                "nonce": 0,
                "deadline": deadline
            }
        }

        text_encoded = encode_typed_data(full_message=permit_data)
        sing_data = self.client.w3.eth.account.sign_message(text_encoded,
                                                            private_key=self.client.private_key)

        return deadline, sing_data.v, hex(sing_data.r), hex(sing_data.s)

    async def get_min_amount_out(self, pool_address: str, from_token_address: str, amount_in_wei: int):
        pool_contract = self.client.get_contract(pool_address, SYNCSWAP_ABI['classic_pool'])
        min_amount_out = await pool_contract.functions.getAmountOut(
            from_token_address,
            amount_in_wei,
            self.client.address
        ).call()

        return int(min_amount_out - (min_amount_out / 100 * SLIPPAGE))

    @helper
    @gas_checker
    async def swap(self, swapdata: tuple = None, paymaster_mode:bool = False):
        if swapdata:
            from_token_name, to_token_name, amount, amount_in_wei = swapdata
        else:
            from_token_name, to_token_name, amount, amount_in_wei = 'ETH', 'USDC', 0.0001, int(0.0001 * 10 ** 18)#await self.client.get_auto_amount()

        self.logger_msg(*self.client.acc_info, msg=f'Swap on SyncSwap: {amount} {from_token_name} -> {to_token_name}')

        from_token_address = TOKENS_PER_CHAIN[self.network][from_token_name]
        to_token_address = TOKENS_PER_CHAIN[self.network][to_token_name]

        withdraw_mode = 2
        deadline = int(time()) + 1800
        pool_address = await self.pool_factory_contract.functions.getPool(from_token_address, to_token_address).call()
        min_amount_out = await self.get_min_amount_out(pool_address, from_token_address, amount_in_wei)

        #await self.client.price_impact_defender(from_token_name, amount, to_token_name, min_amount_out)

        if from_token_name != 'ETH':
            await self.client.check_for_approved(
                from_token_address, SYNCSWAP_CONTRACTS[self.network]['router'], amount_in_wei
            )

        swap_data = abi.encode(['address', 'address', 'uint8'],
                               [from_token_address, self.client.address, withdraw_mode])

        steps = [
            pool_address,
            self.client.w3.to_hex(swap_data),
            ZERO_ADDRESS,
            '0x',
            True,
        ]

        paths = [
            [steps],
            from_token_address if from_token_name != 'ETH' else ZERO_ADDRESS,
            amount_in_wei
        ]

        # [
        #     {
        #         "steps": [
        #             {
        #                 "pool": "0x80115c708E12eDd42E504c1cD52Aea96C547c05c",
        #                 "data": "0x0000000000000000000000005aea5775959fbc2557cc8789bc1bf90a239d9a910000000000000000000000005f1a69ec0b4860ff0fb7da21fdd4e2c5837d14ca0000000000000000000000000000000000000000000000000000000000000001",
        #                 "callback": "0x0000000000000000000000000000000000000000",
        #                 "callbackData": "0x",
        #                 "useVault": false
        #             }
        #         ],
        #         "tokenIn": "0x0000000000000000000000000000000000000000",
        #         "amountIn": 100000000000000
        #     }
        # ]

        tx_params = await self.client.prepare_transaction(value=amount_in_wei if from_token_name == 'ETH' else 0)

        if self.client.network.name == 'Scroll' and from_token_name != 'ETH':
            transaction = await self.router_contract.functions.swapWithPermit(
                paths,
                min_amount_out,
                deadline,
                [
                    from_token_address,
                    2 ** 256 - 1,
                    *(await self.get_swap_permit(from_token_name))
                ]
            ).build_transaction(tx_params)
        else:
            transaction = await self.router_contract.functions.swap(
                [paths],
                min_amount_out,
                deadline,
            ).build_transaction(tx_params)

        if paymaster_mode:
            fee_token_name = {
                0: 'USDT',
                1: 'USDC'
            }[ZKSYNC_PAYMASTER_TOKEN]

            fee_token_address = TOKENS_PER_CHAIN[self.client.network.name][fee_token_name]
            min_allowance = int(2000 * 10 ** 6)
            inner_input = self.client.w3.to_hex(abi.encode(['uint64'], [100]))

            paymaster_input = self.paymaster_contract.encodeABI(
                fn_name='approvalBased',
                args=(
                    fee_token_address,
                    min_allowance,
                    inner_input
                )
            )

            typed_data = {
                "types": {
                    "Transaction": [
                        {
                            "name": "txType",
                            "type": "uint256"
                        },
                        {
                            "name": "from",
                            "type": "uint256"
                        },
                        {
                            "name": "to",
                            "type": "uint256"
                        },
                        {
                            "name": "gasLimit",
                            "type": "uint256"
                        },
                        {
                            "name": "gasPerPubdataByteLimit",
                            "type": "uint256"
                        },
                        {
                            "name": "maxFeePerGas",
                            "type": "uint256"
                        },
                        {
                            "name": "maxPriorityFeePerGas",
                            "type": "uint256"
                        },
                        {
                            "name": "paymaster",
                            "type": "uint256"
                        },
                        {
                            "name": "nonce",
                            "type": "uint256"
                        },
                        {
                            "name": "value",
                            "type": "uint256"
                        },
                        {
                            "name": "data",
                            "type": "bytes"
                        },
                        {
                            "name": "factoryDeps",
                            "type": "bytes32[]"
                        },
                        {
                            "name": "paymasterInput",
                            "type": "bytes"
                        }
                    ],
                    "EIP712Domain": [
                        {
                            "name": "name",
                            "type": "string"
                        },
                        {
                            "name": "version",
                            "type": "string"
                        },
                        {
                            "name": "chainId",
                            "type": "uint256"
                        }
                    ]
                },
                "domain": {
                    "name": self.client.network.name,
                    "version": "2",
                    "chainId": self.client.chain_id
                },
                "primaryType": "Transaction",
                "message": {
                    "txType": 0x71,
                    "from": int(self.client.address, 16),
                    "to": int(self.router_contract.address, 16),
                    "gasLimit": transaction['gas'],
                    "gasPerPubdataByteLimit": 50000,
                    "maxFeePerGas": transaction['maxFeePerGas'],
                    "maxPriorityFeePerGas": transaction['maxPriorityFeePerGas'],
                    "paymaster": int(self.paymaster_contract.address, 16),
                    "nonce": transaction['nonce'],
                    "value": amount_in_wei if from_token_name == 'ETH' else 0,
                    "data": self.client.w3.to_bytes(hexstr=transaction['data']),
                    "factoryDeps": [],
                    "paymasterInput": self.client.w3.to_bytes(hexstr=paymaster_input)
                }
            }

            signature = self.client.w3.eth.account.sign_typed_data(
                self.client.private_key, full_message=typed_data
            ).signature

            paymaster_additional = self.client.w3.to_hex(signature)[2:] + paymaster_input[2:]
            signed_tx = self.client.w3.eth.account.sign_transaction(transaction, self.client.private_key).rawTransaction
            full_tx = "0x71" + self.client.w3.to_hex(signed_tx)[4:] + paymaster_additional

            return await self.client.send_transaction(send_mode=True, signed_tx=full_tx)

        return await self.client.send_transaction(transaction)

    @helper
    @gas_checker
    async def add_liquidity(self):
        amount, amount_in_wei = await self.client.check_and_get_eth()

        self.logger_msg(
            *self.client.acc_info, msg=f'Add liquidity to SyncSwap USDC/ETH pool: {amount} ETH')

        token_a_address = TOKENS_PER_CHAIN[self.client.network.name]['ETH']
        token_b_address = TOKENS_PER_CHAIN[self.client.network.name]['USDC']

        pool_address = await self.pool_factory_contract.functions.getPool(token_a_address, token_b_address).call()
        pool_contract = self.client.get_contract(pool_address, SYNCSWAP_ABI['classic_pool'])

        total_supply = await pool_contract.functions.totalSupply().call()
        _, reserve_eth = await pool_contract.functions.getReserves().call()
        # fee = await pool_contract.functions.getProtocolFee().call()
        min_lp_amount_out = int(amount_in_wei * total_supply / reserve_eth / 2 * 0.9965)

        inputs = [
            (token_b_address, 0),
            (ZERO_ADDRESS, amount_in_wei)
        ]

        tx_params = await self.client.prepare_transaction(value=amount_in_wei)
        transaction = await self.router_contract.functions.addLiquidity2(
            pool_address,
            inputs,
            abi.encode(['address'], [self.client.address]),
            min_lp_amount_out,
            ZERO_ADDRESS,
            '0x'
        ).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)

    @helper
    @gas_checker
    async def withdraw_liquidity(self):
        self.logger_msg(*self.client.acc_info, msg=f'Withdraw liquidity from SyncSwap')

        token_a_address = TOKENS_PER_CHAIN[self.client.network.name]['ETH']
        token_b_address = TOKENS_PER_CHAIN[self.client.network.name]['USDC']

        pool_address = await self.pool_factory_contract.functions.getPool(token_a_address, token_b_address).call()
        pool_contract = self.client.get_contract(pool_address, SYNCSWAP_ABI['classic_pool'])

        liquidity_balance = await pool_contract.functions.balanceOf(self.client.address).call()

        if liquidity_balance != 0:

            await self.client.check_for_approved(
                pool_address, SYNCSWAP_CONTRACTS[self.network]['router'], liquidity_balance)

            total_supply = await pool_contract.functions.totalSupply().call()
            _, reserve_eth = await pool_contract.functions.getReserves().call()
            min_eth_amount_out = int(liquidity_balance * reserve_eth / total_supply * 2 * 0.9965)

            withdraw_mode = 1
            data = abi.encode(['address', 'address', 'uint8'],
                              [token_a_address, self.client.address, withdraw_mode])

            tx_params = await self.client.prepare_transaction()
            transaction = await self.router_contract.functions.burnLiquiditySingle(
                pool_address,
                liquidity_balance,
                data,
                min_eth_amount_out,
                ZERO_ADDRESS,
                "0x",
            ).build_transaction(tx_params)

            return await self.client.send_transaction(transaction)

        else:
            raise SoftwareException('Insufficient balance on SyncSwap!')
