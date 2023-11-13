import asyncio
import random

from faker import Faker
from utils.tools import sleep, gas_checker, repeater
from eth_abi import abi
from settings import DESTINATION_L2TELEGRAPH
from modules import Messenger
from config import (
    L2TELEGRAPH_CONTRACTS,
    L2TELEGRAPH_SEND_MESSAGE_ABI,
    L2TELEGRAPH_NFT_BRIDGE_ABI,
    L2TELEGRAPH_DST_CHAIN_MESSENGER_CONTRACTS,
    L2TELEGRAPH_CROSS_CHAIN_CONTRACTS,
    LAYERZERO_NETWORKS_DATA,
)


class L2Telegraph(Messenger):
    def __init__(self, client):
        self.client = client

        self.message_contract = self.client.get_contract(L2TELEGRAPH_CONTRACTS['messager'], L2TELEGRAPH_SEND_MESSAGE_ABI)
        self.nft_contract = self.client.get_contract(L2TELEGRAPH_CONTRACTS['cross_nft'], L2TELEGRAPH_NFT_BRIDGE_ABI)
        dst_data = random.choice(list(DESTINATION_L2TELEGRAPH))
        self.dst_chain_name, self.dst_chain_id, _, _ = LAYERZERO_NETWORKS_DATA[dst_data]

    async def get_nft_id(self, tx_hash: bytes):
        tx_receipt = await self.client.w3.eth.get_transaction_receipt(tx_hash)
        nft_id = int((tx_receipt.logs[2].topics[3]).hex(), 16)
        if not nft_id:
            return int((tx_receipt.logs[3].topics[3]).hex(), 16)
        return nft_id

    @repeater
    @gas_checker
    async def send_message(self):

        self.client.logger.info(
            f'{self.client.info} Send message on L2Telegraph to {self.dst_chain_name.capitalize()}')

        adapter_params = abi.encode(["uint16", "uint"],
                                    [2, 250000])

        payload = abi.encode(["uint8", "string"],
                             [2, "okokokokokokokokokokokokokokokokokokokok"])

        adapter_params, payload = self.client.w3.to_hex(adapter_params[30:]), self.client.w3.to_hex(payload[30:])

        estimate_fees = (await self.message_contract.functions.estimateFees(
            self.dst_chain_id,
            self.client.address,
            payload,
            False,
            adapter_params
        ).call())[0]

        value = estimate_fees + 250000000000000

        tx_params = await self.client.prepare_transaction(value=value)

        transaction = await self.message_contract.functions.sendMessage(
            Faker().word(),
            self.dst_chain_id,
            L2TELEGRAPH_DST_CHAIN_MESSENGER_CONTRACTS[self.dst_chain_name] + L2TELEGRAPH_CONTRACTS['messager'][2:]
        ).build_transaction(tx_params)

        tx_hash = await self.client.send_transaction(transaction)

        return await self.client.verify_transaction(tx_hash)

    @repeater
    @gas_checker
    async def mint_and_bridge(self):
        self.client.logger.info(
            f"{self.client.info} Mint and bridge NFT on L2telegraph. Price for mint: 0.0005 ETH")

        mint_price = 500000000000000

        adapter_params = abi.encode(["uint16", "uint"],
                                    [2, 400000])

        payload = abi.encode(["uint8", "string"],
                             [2, "0x36a358b3Ba1FB368E35b71ea40c7f4Ab89bFd8e1"])

        adapter_params, payload = self.client.w3.to_hex(adapter_params[30:]), self.client.w3.to_hex(payload[30:])

        estimate_fees = (await self.message_contract.functions.estimateFees(
            self.dst_chain_id,
            self.client.address,
            payload,
            False,
            adapter_params
        ).call())[0]

        value = estimate_fees + 100000000000000

        await asyncio.sleep(1)

        self.client.logger.info(f"{self.client.info} Bridge fee: {(value / 10 ** 18):.6f} ETH")

        if await self.client.w3.eth.get_balance(self.client.address) > (mint_price + value):

            tx_params = await self.client.prepare_transaction(value=mint_price)

            transaction = await self.nft_contract.functions.mint().build_transaction(tx_params)

            tx_hash = await self.client.send_transaction(transaction)

            await self.client.verify_transaction(tx_hash)

            nft_id = await self.get_nft_id(tx_hash)

            await sleep(self, 5, 8)

            self.client.logger.info(
                f'{self.client.info} Bridge NFT on L2telegraph to {self.dst_chain_name.capitalize()}')

            tx_params = await self.client.prepare_transaction(value=value)

            transaction = await self.nft_contract.functions.crossChain(
                self.dst_chain_id,
                L2TELEGRAPH_CROSS_CHAIN_CONTRACTS[self.dst_chain_name] + L2TELEGRAPH_CONTRACTS['cross_nft'][2:],
                nft_id
            ).build_transaction(tx_params)

            tx_hash = await self.client.send_transaction(transaction)

            return await self.client.verify_transaction(tx_hash)

        else:
            raise RuntimeError('Insufficient balance!')
