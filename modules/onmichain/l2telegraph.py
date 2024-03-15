import asyncio
import random

from faker import Faker

from general_settings import SLEEP_TIME
from modules.interfaces import SoftwareException
from settings import DST_CHAIN_L2TELEGRAPH
from utils.tools import sleep, gas_checker, helper
from eth_abi import encode
from modules import Messenger, Logger
from config import (
    L2TELEGRAPH_SEND_MESSAGE_ABI,
    L2TELEGRAPH_NFT_BRIDGE_ABI,
    L2TELEGRAPH_SRC_CHAIN_MESSENGER_CONTRACTS,
    L2TELEGRAPH_DST_CHAIN_MESSENGER_CONTRACTS,
    L2TELEGRAPH_SRC_CHAIN_BRIDGE_CONTRACTS,
    L2TELEGRAPH_DST_CHAIN_BRIDGE_CONTRACTS,
    LAYERZERO_NETWORKS_DATA, L2TELEGRAPH_ADD_VALUE,
)


class L2Telegraph(Messenger, Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)

        self.network = self.client.network.name
        chain_id_to = random.choice(DST_CHAIN_L2TELEGRAPH)
        self.dst_chain_name, self.dst_chain_id, _, _ = LAYERZERO_NETWORKS_DATA[chain_id_to]

    async def get_nft_id(self, tx_hash):
        tx_receipt = await self.client.w3.eth.get_transaction_receipt(tx_hash)

        if self.client.network.name == 'zkSync':
            nft_id = int((tx_receipt.logs[2].topics[3]).hex(), 16)
            if not nft_id:
                nft_id = int((tx_receipt.logs[3].topics[3]).hex(), 16)
        elif self.client.network.name == 'Polygon':
            nft_id = int((tx_receipt.logs[1].topics[3]).hex(), 16)
        else:
            nft_id = int((tx_receipt.logs[0].topics[3]).hex(), 16)
        return nft_id

    @helper
    @gas_checker
    async def send_message(self):
        self.logger_msg(
            *self.client.acc_info,
            msg=f'Send message on L2Telegraph from {self.client.network.name} to {self.dst_chain_name}')

        message_contract = self.client.get_contract(
            L2TELEGRAPH_SRC_CHAIN_MESSENGER_CONTRACTS[self.network],
            L2TELEGRAPH_SEND_MESSAGE_ABI
        )

        adapter_params = encode(["uint16", "uint"],
                                [2, 250000])

        payload = encode(["uint8", "string"],
                         [2, "okokokokokokokokokokokokokokokokokokokok"])

        adapter_params, payload = self.client.w3.to_hex(adapter_params[30:]), self.client.w3.to_hex(payload[30:])

        estimate_fees = (await message_contract.functions.estimateFees(
            self.dst_chain_id,
            self.client.address,
            payload,
            False,
            adapter_params
        ).call())[0]

        add_value = L2TELEGRAPH_ADD_VALUE.get(self.network, 0.00025 * 10 ** 18)

        value = round(int(estimate_fees + add_value), 8)

        tx_params = await self.client.prepare_transaction(value=value)

        trusted_remote = (L2TELEGRAPH_DST_CHAIN_MESSENGER_CONTRACTS[self.dst_chain_name] +
                          L2TELEGRAPH_SRC_CHAIN_MESSENGER_CONTRACTS[self.network][2:])

        transaction = await message_contract.functions.sendMessage(
            Faker().word(),
            self.dst_chain_id,
            trusted_remote
        ).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)

    @helper
    @gas_checker
    async def mint_and_bridge(self):
        self.logger_msg(
            *self.client.acc_info,
            msg=f"Mint and bridge NFT L2Telegraph on {self.client.network.name}. Price for mint: 0.0005 ETH")

        nft_contract = self.client.get_contract(
            L2TELEGRAPH_SRC_CHAIN_BRIDGE_CONTRACTS[self.network],
            L2TELEGRAPH_NFT_BRIDGE_ABI
        )

        mint_price = 500000000000000

        adapter_params = encode(["uint16", "uint"],
                                [2, 400000])

        payload = encode(["uint8", "string"],
                         [2, "0x36a358b3Ba1FB368E35b71ea40c7f4Ab89bFd8e1"])

        adapter_params, payload = self.client.w3.to_hex(adapter_params[30:]), self.client.w3.to_hex(payload[30:])

        estimate_fees = (await nft_contract.functions.estimateFees(
            self.dst_chain_id,
            self.client.address,
            payload,
            False,
            adapter_params
        ).call())[0]

        value = round(estimate_fees, 8)

        await asyncio.sleep(1)

        self.logger_msg(*self.client.acc_info, msg=f"Bridge fee: {(value / 10 ** 18):.6f} ETH")

        if await self.client.w3.eth.get_balance(self.client.address) > (mint_price + value):

            tx_params = await self.client.prepare_transaction(value=mint_price)

            transaction = await nft_contract.functions.mint().build_transaction(tx_params)

            tx_hash = await self.client.send_transaction(transaction, need_hash=True)

            nft_id = await self.get_nft_id(tx_hash)

            await sleep(self, *SLEEP_TIME)

            self.logger_msg(
                *self.client.acc_info,
                msg=f'Bridge NFT on L2telegraph from {self.client.network.name} to {self.dst_chain_name}')

            tx_params = await self.client.prepare_transaction(value=value)
            salt = (L2TELEGRAPH_DST_CHAIN_BRIDGE_CONTRACTS[self.dst_chain_name] +
                    L2TELEGRAPH_SRC_CHAIN_BRIDGE_CONTRACTS[self.network][2:])

            transaction = await nft_contract.functions.crossChain(
                self.dst_chain_id,
                salt,
                nft_id
            ).build_transaction(tx_params)

            return await self.client.send_transaction(transaction)

        else:
            raise SoftwareException('Insufficient balance for mint!')
