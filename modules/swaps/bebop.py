import time
import random

from eth_account.messages import encode_typed_data
from modules import DEX, Logger, Client, RequestClient
from config import ETH_MASK
from modules.interfaces import SoftwareException
from utils.tools import gas_checker, helper
from config import BEBOP_CONTRACTS, TOKENS_PER_CHAIN
from settings import BEBOP_DOUBLESWAP_AMOUNTS, BEBOP_DOUBLESWAP_FROM_TOKEN_NAMES, BEBOP_DOUBLESWAP_TO_TOKEN_NAME


class Bebop(DEX, Logger, RequestClient):
    def __init__(self, client: Client):
        self.client = client
        Logger.__init__(self)
        self.network = self.client.network.name
        self.router_address = BEBOP_CONTRACTS[self.network]['router']
        self.spender_address = BEBOP_CONTRACTS[self.network]['spender']

    async def get_data_to_sign(self, from_token_address: str, to_token_address: str, amount_in_wei: str):
        url = f'https://api.bebop.xyz/router/{self.client.network.name.lower()}/v1/quote'

        params = {
            'buy_tokens': to_token_address,
            'sell_tokens': from_token_address,
            'taker_address': self.client.address,
            'receiver_address': self.client.address,
            'source': 'bebop.xyz',
            'approval_type': 'Permit2',
            'sell_amounts': amount_in_wei
        }

        response = await self.make_request(url=url, params=params)

        if response.get('error'):
            raise SoftwareException(response['error']['message'])

        bebop_data = {
            'min_amount_out': int(response['routes'][0]['quote']['buyTokens'][to_token_address]['amount']),
            'data_to_sign': response['routes'][0]['quote']['toSign'],
            'quote_id': response['routes'][0]['quote']['quoteId'],
            'route_type': response['routes'][0]['type'],
            'required_signatures': response['routes'][0]['quote']['requiredSignatures']
        }

        return bebop_data

    async def get_fee_permit_signature(self, required_signatures: list, order_type='single'):
        deadline = int(time.time() + 360)

        if order_type == 'single':
            message = {
                "details": [
                    {
                        "token": required_signatures[0],
                        "amount": "1461501637330902918203684832716283019655932542975",
                        "expiration": deadline,
                        "nonce": 0
                    }
                ],
                "spender": self.router_address,
                "sigDeadline": f"{deadline}"
            }
        else:
            message = {
                "details": [
                    {
                        "token": required_signatures[0],
                        "amount": "1461501637330902918203684832716283019655932542975",
                        "expiration": deadline,
                        "nonce": 1
                    },
                    {
                        "token": required_signatures[1],
                        "amount": "1461501637330902918203684832716283019655932542975",
                        "expiration": deadline,
                        "nonce": 0
                    }
                ],
                "spender": self.router_address,
                "sigDeadline": f"{deadline}"
            }

        typed_data = {
            "types": {
                "EIP712Domain": [
                    {
                        "name": "name",
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
                ],
                "PermitBatch": [
                    {
                        "name": "details",
                        "type": "PermitDetails[]"
                    },
                    {
                        "name": "spender",
                        "type": "address"
                    },
                    {
                        "name": "sigDeadline",
                        "type": "uint256"
                    }
                ],
                "PermitDetails": [
                    {
                        "name": "token",
                        "type": "address"
                    },
                    {
                        "name": "amount",
                        "type": "uint160"
                    },
                    {
                        "name": "expiration",
                        "type": "uint48"
                    },
                    {
                        "name": "nonce",
                        "type": "uint48"
                    }
                ]
            },
            "primaryType": "PermitBatch",
            "domain": {
                "name": "Permit2",
                "chainId": self.client.chain_id,
                "verifyingContract": "0x000000000022d473030f116ddee9f6b43ac78ba3"
            },
            "message": message
        }

        text_encoded = encode_typed_data(full_message=typed_data)
        sing_data = self.client.w3.eth.account.sign_message(text_encoded, private_key=self.client.private_key)

        return self.client.w3.to_hex(sing_data.signature), deadline

    async def get_order_data(self, from_token_address, to_token_address, amount_in_wei, order_type='single'):
        bebop_data = await self.get_data_to_sign(from_token_address, to_token_address, amount_in_wei)

        min_amount_out = bebop_data['min_amount_out']
        data_to_sign = bebop_data['data_to_sign']
        quote_id = bebop_data['quote_id']
        route_type = bebop_data['route_type']
        required_signatures = bebop_data['required_signatures']

        if order_type == 'single':
            if route_type == "PMMv3":
                single_pmmv3_typed_data = {
                    "types": {
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
                        ],
                        "SingleOrder": [
                            {
                                "name": "partner_id",
                                "type": "uint64"
                            },
                            {
                                "name": "expiry",
                                "type": "uint256"
                            },
                            {
                                "name": "taker_address",
                                "type": "address"
                            },
                            {
                                "name": "maker_address",
                                "type": "address"
                            },
                            {
                                "name": "maker_nonce",
                                "type": "uint256"
                            },
                            {
                                "name": "taker_token",
                                "type": "address"
                            },
                            {
                                "name": "maker_token",
                                "type": "address"
                            },
                            {
                                "name": "taker_amount",
                                "type": "uint256"
                            },
                            {
                                "name": "maker_amount",
                                "type": "uint256"
                            },
                            {
                                "name": "receiver",
                                "type": "address"
                            },
                            {
                                "name": "packed_commands",
                                "type": "uint256"
                            }
                        ]
                    },
                    "primaryType": "SingleOrder",
                    "domain": {
                        "name": "BebopSettlement",
                        "version": "2",
                        "chainId": self.client.chain_id,
                        "verifyingContract": self.router_address
                    },
                    "message": {
                        **data_to_sign
                    }
                }
                typed_data = single_pmmv3_typed_data
            else:
                single_jam_typed_data = {
                    "types": {
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
                        ],
                        "JamOrder": [
                            {
                                "name": "taker",
                                "type": "address"
                            },
                            {
                                "name": "receiver",
                                "type": "address"
                            },
                            {
                                "name": "expiry",
                                "type": "uint256"
                            },
                            {
                                "name": "nonce",
                                "type": "uint256"
                            },
                            {
                                "name": "executor",
                                "type": "address"
                            },
                            {
                                "name": "minFillPercent",
                                "type": "uint16"
                            },
                            {
                                "name": "hooksHash",
                                "type": "bytes32"
                            },
                            {
                                "name": "sellTokens",
                                "type": "address[]"
                            },
                            {
                                "name": "buyTokens",
                                "type": "address[]"
                            },
                            {
                                "name": "sellAmounts",
                                "type": "uint256[]"
                            },
                            {
                                "name": "buyAmounts",
                                "type": "uint256[]"
                            },
                            {
                                "name": "sellNFTIds",
                                "type": "uint256[]"
                            },
                            {
                                "name": "buyNFTIds",
                                "type": "uint256[]"
                            },
                            {
                                "name": "sellTokenTransfers",
                                "type": "bytes"
                            },
                            {
                                "name": "buyTokenTransfers",
                                "type": "bytes"
                            }
                        ]
                    },
                    "primaryType": "JamOrder",
                    "domain": {
                        "name": "JamSettlement",
                        "version": "1",
                        "chainId": self.client.chain_id,
                        "verifyingContract": self.router_address
                    },
                    "message": {
                        **data_to_sign
                    }
                }
                typed_data = single_jam_typed_data
        else:
            if route_type == "PMMv3":
                multi_pmmv3_typed_data = {
                    "types": {
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
                        ],
                        "MultiOrder": [
                            {
                                "name": "partner_id",
                                "type": "uint64"
                            },
                            {
                                "name": "expiry",
                                "type": "uint256"
                            },
                            {
                                "name": "taker_address",
                                "type": "address"
                            },
                            {
                                "name": "maker_address",
                                "type": "address"
                            },
                            {
                                "name": "maker_nonce",
                                "type": "uint256"
                            },
                            {
                                "name": "taker_tokens",
                                "type": "address[]"
                            },
                            {
                                "name": "maker_tokens",
                                "type": "address[]"
                            },
                            {
                                "name": "taker_amounts",
                                "type": "uint256[]"
                            },
                            {
                                "name": "maker_amounts",
                                "type": "uint256[]"
                            },
                            {
                                "name": "receiver",
                                "type": "address"
                            },
                            {
                                "name": "commands",
                                "type": "bytes"
                            }
                        ]
                    },
                    "primaryType": "MultiOrder",
                    "domain": {
                        "name": "BebopSettlement",
                        "version": "2",
                        "chainId": self.client.chain_id,
                        "verifyingContract": self.router_address
                    },
                    "message": {
                        **data_to_sign
                    }
                }
                typed_data = multi_pmmv3_typed_data
            else:
                multi_jam_typed_data = {
                    "types": {
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
                        ],
                        "JamOrder": [
                            {
                                "name": "taker",
                                "type": "address"
                            },
                            {
                                "name": "receiver",
                                "type": "address"
                            },
                            {
                                "name": "expiry",
                                "type": "uint256"
                            },
                            {
                                "name": "nonce",
                                "type": "uint256"
                            },
                            {
                                "name": "executor",
                                "type": "address"
                            },
                            {
                                "name": "minFillPercent",
                                "type": "uint16"
                            },
                            {
                                "name": "hooksHash",
                                "type": "bytes32"
                            },
                            {
                                "name": "sellTokens",
                                "type": "address[]"
                            },
                            {
                                "name": "buyTokens",
                                "type": "address[]"
                            },
                            {
                                "name": "sellAmounts",
                                "type": "uint256[]"
                            },
                            {
                                "name": "buyAmounts",
                                "type": "uint256[]"
                            },
                            {
                                "name": "sellNFTIds",
                                "type": "uint256[]"
                            },
                            {
                                "name": "buyNFTIds",
                                "type": "uint256[]"
                            },
                            {
                                "name": "sellTokenTransfers",
                                "type": "bytes"
                            },
                            {
                                "name": "buyTokenTransfers",
                                "type": "bytes"
                            }
                        ]
                    },
                    "primaryType": "JamOrder",
                    "domain": {
                        "name": "JamSettlement",
                        "version": "1",
                        "chainId": self.client.chain_id,
                        "verifyingContract": self.router_address
                    },
                    "message": {
                        **data_to_sign
                    }
                }
                typed_data = multi_jam_typed_data

        text_encoded = encode_typed_data(full_message=typed_data)
        sign_data = self.client.w3.eth.account.sign_message(text_encoded, private_key=self.client.private_key)

        order_data = {
            'min_amount_out': min_amount_out,
            'order_signature': self.client.w3.to_hex(sign_data.signature),
            'quote_id': quote_id,
            'required_signatures': required_signatures,
        }

        return order_data

    @helper
    @gas_checker
    async def swap(self, swapdata: tuple = None):
        from functions import wrap_eth, unwrap_eth

        url = f'https://api.bebop.xyz/pmm/{self.client.network.name.lower()}/v3/order'

        if not swapdata:
            from_token_name, to_token_name, amount, amount_in_wei = await self.client.get_auto_amount()
        else:
            from_token_name, to_token_name, amount, amount_in_wei = swapdata

        self.logger_msg(*self.client.acc_info, msg=f'Swap on bebop: {amount} {from_token_name} -> {to_token_name}')

        from_token_address = TOKENS_PER_CHAIN[self.network][from_token_name]
        to_token_address = TOKENS_PER_CHAIN[self.network][to_token_name]

        order_data = await self.get_order_data(from_token_address, to_token_address, amount_in_wei)
        min_amount_out = order_data['min_amount_out']
        order_signature = order_data['order_signature']
        quote_id = order_data['quote_id']
        required_signatures = order_data['required_signatures']

        await self.client.price_impact_defender(from_token_name, amount, to_token_name, min_amount_out)

        if from_token_name == 'ETH':
            _, wnative_balance, _ = await self.client.get_token_balance(f'W{self.client.token}')

            if wnative_balance < amount:
                self.logger_msg(*self.client.acc_info, msg=f'Need wrap ETH -> WETH, launch wrap module...')
                await wrap_eth(self.client.account_name, self.client.private_key, self.client.network,
                               self.client.proxy_init, amount_in_wei)
            else:
                self.logger_msg(
                    *self.client.acc_info,
                    msg=f'You have enough wrapped native: {wnative_balance:.6f} W{self.client.token}',
                    type_msg='success'
                )

            await self.client.check_for_approved(
                TOKENS_PER_CHAIN[self.network]['WETH'], self.spender_address, amount_in_wei * 2
            )

        if from_token_name != 'ETH':
            await self.client.check_for_approved(from_token_address, self.spender_address, amount_in_wei)

        payload = {
            'signature': order_signature,
            'quote_id': quote_id,
        }

        if required_signatures:
            permit_signature, deadline = await self.get_fee_permit_signature(required_signatures)
            payload["permit2"] = {
                "signature": permit_signature,
                "approvals_deadline": deadline,
                "token_addresses": [
                    required_signatures[0]
                ],
                "token_nonces": [
                    0
                ]
            }

        response = (await self.make_request(method="POST", url=url, json=payload))

        if response.get('error'):
            raise SoftwareException(response['error']['message'])
        elif response['status'] == 'Success':
            tx_hash = response['txHash']
        else:
            raise SoftwareException(f'Bad request to Bebop API(Order): {response}')

        result = await self.client.send_transaction(tx_hash=tx_hash)

        if from_token_name != 'ETH':
            await unwrap_eth(self.client.account_name, self.client.private_key, self.client.network,
                             self.client.proxy_init)

        return result

    @helper
    @gas_checker
    async def double_swap(self):
        from functions import wrap_eth

        first_token_name, second_token_name = random.sample(BEBOP_DOUBLESWAP_FROM_TOKEN_NAMES, 2)

        first_amount_in_wei, first_amount, _ = await self.client.get_token_balance(
            token_address=TOKENS_PER_CHAIN[self.network][first_token_name], token_name=first_token_name
        )

        second_amount_in_wei, second_amount, _ = await self.client.get_token_balance(
            token_address=TOKENS_PER_CHAIN[self.network][second_token_name], token_name=second_token_name
        )

        if isinstance(BEBOP_DOUBLESWAP_AMOUNTS[0], str):
            start = int(BEBOP_DOUBLESWAP_AMOUNTS[0])
            end = int(BEBOP_DOUBLESWAP_AMOUNTS[1])
            percent = random.randint(start, end)
            first_amount = round(first_amount * (percent / 100), 6)
            first_amount_in_wei = int(first_amount_in_wei * (percent / 100))
            second_amount = round(second_amount * (percent / 100), 6)
            second_amount_in_wei = int(second_amount_in_wei * (percent / 100))
        else:
            start = float(BEBOP_DOUBLESWAP_AMOUNTS[0])
            end = float(BEBOP_DOUBLESWAP_AMOUNTS[0])
            random_float = random.uniform(start, end)
            first_amount = random_float
            first_token_decimals = await self.client.get_decimals(
                token_address=TOKENS_PER_CHAIN[self.network][first_token_name], token_name=first_token_name
            )
            first_amount_in_wei = self.client.to_wei(first_amount, first_token_decimals)
            second_amount = random_float
            second_token_decimals = await self.client.get_decimals(
                token_address=TOKENS_PER_CHAIN[self.network][second_token_name], token_name=second_token_name
            )
            second_amount_in_wei = self.client.to_wei(second_amount, second_token_decimals)

        from_token_address = (f'{TOKENS_PER_CHAIN[self.network][first_token_name]},'
                              f'{TOKENS_PER_CHAIN[self.network][second_token_name]}')

        if BEBOP_DOUBLESWAP_TO_TOKEN_NAME == 'ETH':
            to_token_address = ETH_MASK
        else:
            to_token_address = TOKENS_PER_CHAIN[self.network][BEBOP_DOUBLESWAP_TO_TOKEN_NAME]

        both_amount_in_wei = f'{first_amount_in_wei},{second_amount_in_wei}'

        url = f'https://api.bebop.xyz/pmm/{self.client.network.name.lower()}/v3/order'

        self.logger_msg(*self.client.acc_info,
                        msg=f'Double swap on bebop: {first_amount} {first_token_name} + {second_amount} '
                            f'{second_token_name} -> {BEBOP_DOUBLESWAP_TO_TOKEN_NAME}')

        if first_token_name == 'ETH' or second_token_name == 'ETH':
            if first_token_name == 'ETH':
                amount = first_amount
                amount_in_wei = first_amount_in_wei
            else:
                amount = second_amount
                amount_in_wei = second_amount_in_wei

            _, wnative_balance, _ = await self.client.get_token_balance(f'W{self.client.token}')

            if wnative_balance < amount:
                self.logger_msg(*self.client.acc_info, msg=f'Need wrap ETH -> WETH, launch wrap module...')
                await wrap_eth(self.client.account_name, self.client.private_key, self.client.network,
                               self.client.proxy_init, amount_in_wei)
            else:
                self.logger_msg(
                    *self.client.acc_info,
                    msg=f'You have enough wrapped native: {wnative_balance:.6f} W{self.client.token}',
                    type_msg='success'
                )

            await self.client.check_for_approved(
                TOKENS_PER_CHAIN[self.network]['WETH'], self.spender_address, amount_in_wei * 2
            )

        if first_token_name != 'ETH':
            await self.client.check_for_approved(
                TOKENS_PER_CHAIN[self.network][first_token_name], self.spender_address, first_amount_in_wei
            )

        if second_token_name != 'ETH':
            await self.client.check_for_approved(
                TOKENS_PER_CHAIN[self.network][second_token_name], self.spender_address, second_amount_in_wei
            )

        order_data = await self.get_order_data(
            from_token_address, to_token_address, both_amount_in_wei, order_type="multi"
        )

        order_signature = order_data['order_signature']
        quote_id = order_data['quote_id']
        required_signatures = order_data['required_signatures']

        payload = {
            'signature': order_signature,
            'quote_id': quote_id,
        }

        if len(required_signatures) == 1:
            permit_signature, deadline = await self.get_fee_permit_signature(required_signatures)
            payload["permit2"] = {
                "signature": permit_signature,
                "approvals_deadline": deadline,
                "token_addresses": [
                    required_signatures[0]
                ],
                "token_nonces": [
                    0
                ]
            }
        elif len(required_signatures) == 2:
            permit_signature, deadline = await self.get_fee_permit_signature(required_signatures, order_type='multi')
            payload["permit2"] = {
                "signature": permit_signature,
                "approvals_deadline": deadline,
                "token_addresses": [
                    required_signatures[0],
                    required_signatures[1]
                ],
                "token_nonces": [
                    1,
                    0
                ]
            }

        response = (await self.make_request(method="POST", url=url, json=payload))

        if response.get('error'):
            raise SoftwareException(response['error']['message'])
        elif response['status'] == 'Success':
            tx_hash = response['txHash']
        else:
            raise SoftwareException(f'Bad request to Bebop API(Order): {response}')

        return await self.client.send_transaction(tx_hash=tx_hash)
