import asyncio
import random
import time

from eth_account.messages import encode_typed_data
from modules import DEX, Logger, Client, RequestClient
from config import ETH_MASK
from modules.interfaces import SoftwareException
from utils.tools import gas_checker, helper
from config import BEBOP_CONTRACTS, TOKENS_PER_CHAIN, BEBOP_TOKENS_PER_CHAIN, PERMIT2_ABI
from settings import BEBOP_MULTISWAP_AMOUNT
from general_settings import SLIPPAGE


class Bebop(DEX, Logger, RequestClient):
    def __init__(self, client: Client):
        self.client = client
        Logger.__init__(self)
        self.network = self.client.network.name
        self.router_addresses = BEBOP_CONTRACTS['router']
        self.spender_address = BEBOP_CONTRACTS['spender']
        self.balance_manager_address = BEBOP_CONTRACTS['balance_manager']

    @staticmethod
    async def get_buy_tokens_ratios(number_of_tokens_to_buy):

        first_ratio = round(random.uniform(0.01, round(1 / number_of_tokens_to_buy, 2) * 2 -
                                           (0.01 * (number_of_tokens_to_buy - 1))), 2)
        ratio = [first_ratio]

        for i in range(1, number_of_tokens_to_buy - 1):
            ratio.append(
                round(random.uniform(0.01, min(1 - sum(ratio[0:i]) - (0.01 * (number_of_tokens_to_buy - i - 1)),
                                               round(1 / number_of_tokens_to_buy, 2) * 2)), 2))

        ratio.append(round(1 - sum(ratio), 2))

        return ratio

    async def get_random_to_token_names(self):
        return random.sample(list(BEBOP_TOKENS_PER_CHAIN[self.network].keys()), random.randint(2, 5))

    async def get_data_to_sign(self, from_token_addresses: str, to_token_addresses: str, amounts_in_wei: str,
                               order_type: str):
        url = f'https://api.bebop.xyz/router/{self.client.network.name.lower() if self.client.network.name != "BNB Chain" else "bsc"}/v1/quote'

        params = {
            'buy_tokens': to_token_addresses,
            'sell_tokens': from_token_addresses,
            'taker_address': self.client.address,
            'source': 'bebop.xyz',
            'approval_type': 'Permit2',
            'sell_amounts': amounts_in_wei,
            'slippage': SLIPPAGE
        }

        if order_type == 'multi' and ',' in to_token_addresses:
            params['buy_tokens_ratios'] = str(await self.get_buy_tokens_ratios(
                len(to_token_addresses.split(',')))).replace(' ', '')[1:-1]

        response = await self.make_request(url=url, params=params)

        if response.get('error'):
            raise SoftwareException(response['error']['message'])

        try:
            route = random.choice([route for route in response['routes']
                                   if 'success' in route['quote']['status'].lower()])
        except:
            raise SoftwareException('Quote failed')

        bebop_data = {
            'data_to_sign': route['quote']['toSign'],
            'quote_id': route['quote']['quoteId'],
            'route_type': route['type'],
            'required_signatures': route['quote']['requiredSignatures']
        }

        if route['type'] == 'Jam':
            bebop_data['min_amounts_out'] = [int(amount) for amount in route['quote']['toSign']['buyAmounts']]
        else:
            if order_type == 'multi':
                bebop_data['min_amounts_out'] = [int(amount) for amount in route['quote']['toSign']['maker_amounts']]
            else:
                bebop_data['min_amounts_out'] = [int(route['quote']['toSign']['maker_amount'])]

        return bebop_data

    async def get_fee_permit_signature(self, required_signatures: list, route_type: str):
        deadline = int(time.time() + 360)
        permit2_contract = self.client.get_contract(self.spender_address, PERMIT2_ABI)

        allowances = await asyncio.gather(*[
            permit2_contract.functions.allowance(
                self.client.address,
                required_signature,
                self.client.w3.to_checksum_address(self.balance_manager_address) if route_type == 'Jam'
                else self.client.w3.to_checksum_address(self.router_addresses[route_type])
            ).call() for required_signature in required_signatures
        ])

        nonces = [allowance[2] for allowance in allowances]

        message = {
            "details": [
                {
                    "token": required_signatures[i],
                    "amount": "1461501637330902918203684832716283019655932542975",
                    "expiration": deadline,
                    "nonce": nonces[i]
                }
                for i in range(len(required_signatures))
            ],
            "spender": self.balance_manager_address if route_type == 'Jam' else self.router_addresses[route_type],
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
                "verifyingContract": self.spender_address
            },
            "message": message
        }

        text_encoded = encode_typed_data(full_message=typed_data)
        sing_data = self.client.w3.eth.account.sign_message(text_encoded, private_key=self.client.private_key)

        return self.client.w3.to_hex(sing_data.signature), deadline, nonces

    async def get_order_data(self, from_token_addresses, to_token_addresses, amounts_in_wei, order_type='single'):
        bebop_data = await self.get_data_to_sign(from_token_addresses, to_token_addresses, amounts_in_wei, order_type)

        min_amounts_out = bebop_data['min_amounts_out']
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
                        "verifyingContract": self.router_addresses[route_type]
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
                        "verifyingContract": self.router_addresses[route_type]
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
                        "verifyingContract": self.router_addresses[route_type]
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
                        "verifyingContract": self.router_addresses[route_type]
                    },
                    "message": {
                        **data_to_sign
                    }
                }
                typed_data = multi_jam_typed_data

        text_encoded = encode_typed_data(full_message=typed_data)
        sign_data = self.client.w3.eth.account.sign_message(text_encoded, private_key=self.client.private_key)

        order_data = {
            'min_amounts_out': min_amounts_out,
            'order_signature': self.client.w3.to_hex(sign_data.signature),
            'quote_id': quote_id,
            'route_type': route_type,
            'required_signatures': required_signatures,
        }

        return order_data

    @helper
    @gas_checker
    async def swap(self, swapdata: tuple = None):
        from functions import wrap_eth

        if not swapdata:
            from_token_name, to_token_name, amount, amount_in_wei = await self.client.get_auto_amount()
        else:
            from_token_name, to_token_name, amount, amount_in_wei = swapdata

        self.logger_msg(*self.client.acc_info, msg=f'Swap on bebop: {amount} {from_token_name} -> {to_token_name}')

        from_token_address = TOKENS_PER_CHAIN[self.network][from_token_name]
        to_token_address = TOKENS_PER_CHAIN[self.network][to_token_name] if to_token_name != 'ETH' else ETH_MASK

        if from_token_name == 'ETH':
            _, wnative_balance, _ = await self.client.get_token_balance(f'W{self.client.token}')

            if wnative_balance < amount:
                self.logger_msg(*self.client.acc_info, msg=f'Need wrap ETH -> WETH, launch wrap module...')
                await wrap_eth(self.client.account_name, self.client.private_key, self.client.network,
                               self.client.proxy_init, amount_in_wei)
            else:
                self.logger_msg(
                    *self.client.acc_info,
                    msg=f'You have enough wrapped native',
                    type_msg='success'
                )

            await self.client.check_for_approved(
                TOKENS_PER_CHAIN[self.network]['WETH'], self.spender_address, amount_in_wei * 2
            )

        if from_token_name != 'ETH':
            await self.client.check_for_approved(from_token_address, self.spender_address, amount_in_wei)

        order_data = await self.get_order_data(from_token_address, to_token_address, amount_in_wei)

        return await self.send_order(order_data, (from_token_name, amount, to_token_name))

    @helper
    @gas_checker
    async def one_to_many_swap(self):
        from functions import wrap_eth

        to_token_names = await self.get_random_to_token_names()
        to_token_addresses = ','.join([BEBOP_TOKENS_PER_CHAIN[self.network][to_token_name]
                                       for to_token_name in to_token_names])

        wnative_balance_in_wei, wnative_balance, _ = await self.client.get_token_balance(f'W{self.client.token}')

        if any(isinstance(setting, str) for setting in BEBOP_MULTISWAP_AMOUNT):
            native_balance_in_wei, native_balance, _ = await self.client.get_token_balance(check_native=True)
            percent = round(random.uniform(float(BEBOP_MULTISWAP_AMOUNT[0]), float(BEBOP_MULTISWAP_AMOUNT[1])), 9) / 100

            amount = self.client.custom_round((wnative_balance + native_balance) * percent, 7)
            amount_in_wei = int((wnative_balance_in_wei + native_balance_in_wei) * percent)

        else:
            amount = self.client.round_amount(*BEBOP_MULTISWAP_AMOUNT)
            amount_in_wei = self.client.to_wei(amount)

        msg = f'{amount} {self.client.token} -> {", ".join(to_token_names)}'
        self.logger_msg(*self.client.acc_info, msg=f'Multi swap on Bebop: {msg}')

        if amount_in_wei > wnative_balance_in_wei:
            self.logger_msg(*self.client.acc_info, msg=f'Need wrap {self.client.token} -> W{self.client.token}, '
                                                       f'launch wrap module...')
            await wrap_eth(self.client.account_name, self.client.private_key, self.client.network,
                           self.client.proxy_init, amount_in_wei - wnative_balance_in_wei)
        else:
            self.logger_msg(
                *self.client.acc_info,
                msg=f'You have enough wrapped native',
                type_msg='success'
            )

        await self.client.check_for_approved(
            TOKENS_PER_CHAIN[self.network][f'W{self.client.token}'], self.spender_address, amount_in_wei + 1
        )

        order_data = await self.get_order_data(TOKENS_PER_CHAIN[self.network][f'W{self.client.token}'],
                                               to_token_addresses, amount_in_wei, order_type='multi')

        if await self.send_order(order_data, order_type='multi'):
            return to_token_names

    @helper
    @gas_checker
    async def many_to_one_swap(self, from_token_names: list):
        to_token_addresses = ETH_MASK
        token_balances = await asyncio.gather(
            *[self.client.get_token_balance(token_name=from_token_name,
                                            token_address=BEBOP_TOKENS_PER_CHAIN[self.network][from_token_name])
              for from_token_name in from_token_names]
        )

        amounts = [self.client.custom_round(token_balance[1], 7) for token_balance in token_balances]
        amounts_in_wei = [token_balance[0] for token_balance in token_balances]

        msg = ", ".join([f"{amount} {from_token_name}"
                         for amount, from_token_name
                         in zip(amounts, from_token_names)]) + f' -> {self.client.token}'

        self.logger_msg(*self.client.acc_info, msg=f'Multi swap on Bebop: {msg}')

        for i, token_name in enumerate(from_token_names):
            await self.client.check_for_approved(
                BEBOP_TOKENS_PER_CHAIN[self.network][token_name], self.spender_address, amounts_in_wei[i] + 1
            )

        order_data = await self.get_order_data(
            ','.join([BEBOP_TOKENS_PER_CHAIN[self.network][token_name] for token_name in from_token_names]),
            to_token_addresses, ','.join([str(amount_in_wei) for amount_in_wei in amounts_in_wei]), order_type='multi')

        return await self.send_order(order_data, order_type='multi')

    async def send_order(self, order_data: dict, swap_data: tuple = None, order_type: str = 'single'):
        order_signature = order_data['order_signature']
        quote_id = order_data['quote_id']
        route_type = order_data['route_type']
        required_signatures = order_data['required_signatures']

        if order_type == 'single':
            min_amount_out = order_data['min_amounts_out'][0]
            await self.client.price_impact_defender(*swap_data, min_amount_out)

        payload = {
            'signature': order_signature,
            'quote_id': quote_id,
        }

        if required_signatures:
            permit_signature, deadline, nonces = await self.get_fee_permit_signature(required_signatures, route_type)
            payload["permit2"] = {
                "signature": permit_signature,
                "approvals_deadline": deadline,
                "token_addresses": required_signatures,
                "token_nonces": nonces
            }

        self.logger_msg(*self.client.acc_info, msg=f'Sending order...')

        if route_type == 'Jam':
            url = f'https://api.bebop.xyz/jam/{self.client.network.name.lower() if self.client.network.name != "BNB Chain" else "bsc"}/v1/order'
        else:
            url = f'https://api.bebop.xyz/pmm/{self.client.network.name.lower() if self.client.network.name != "BNB Chain" else "bsc"}/v3/order'

        headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "origin": "https://bebop.xyz",
            "referer": "https://bebop.xyz/",
            "sec-ch-ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
        }

        response = (await self.make_request(method="POST", url=url, headers=headers, json=payload))

        url += '-status'
        params = {
            'quote_id': quote_id
        }

        while True:
            if response.get('error'):
                raise SoftwareException(response['error']['message'])
            elif response['status'] == 'Pending':
                response = (await self.make_request(url=url, params=params))
            elif response['status'] in ('Success', 'Settled'):
                if 'txHash' in response:
                    tx_hash = response['txHash']
                    break
                else:
                    pass
            else:
                raise SoftwareException(f'Bad request to Bebop API(Order): {response}')

            await asyncio.sleep(5)

        return await self.client.send_transaction(tx_hash=tx_hash)
