from time import time
from modules import DEX
from utils.tools import gas_checker, repeater
from settings import SLIPPAGE_PERCENT
from config import (
    ZERO_ADDRESS,
    MAVERICK_ROUTER_ABI,
    MAVERICK_POOL_INFORMATION_ABI,
    MAVERICK_POSITION_ABI,
    MAVERICK_POSITION_INSPECTOR_ABI,
    MAVERICK_POOL_ABI,
    MAVERICK_CONTRACTS,
    ZKSYNC_TOKENS
)


class Maverick(DEX):
    def __init__(self, client):
        self.client = client

        self.router_contract = self.client.get_contract(MAVERICK_CONTRACTS['router'], MAVERICK_ROUTER_ABI)
        self.pool_info_contract = self.client.get_contract(MAVERICK_CONTRACTS['pool_information'],
                                                           MAVERICK_POOL_INFORMATION_ABI)
        self.position_contract = self.client.get_contract(MAVERICK_CONTRACTS['position'], MAVERICK_POSITION_ABI)
        self.position_inspector_contract = self.client.get_contract(MAVERICK_CONTRACTS['position_inspector'],
                                                                    MAVERICK_POSITION_INSPECTOR_ABI)

    async def get_min_amount_out(self, pool_address:str, from_token_name: str, amount_in_wei: int):
        min_amount_out = await self.pool_info_contract.functions.calculateSwap(
            pool_address,
            amount_in_wei,
            True if from_token_name == 'ETH' else False,
            True,
            0
        ).call()

        return int(min_amount_out - (min_amount_out / 100 * SLIPPAGE_PERCENT))

    @staticmethod
    def get_path(from_token_address: str, pool_address:str, to_token_address: str):
        path_data = [from_token_address, pool_address, to_token_address]
        return b"".join((bytes.fromhex(address[2:]) for address in path_data))

    @staticmethod
    def get_pool_address(from_token_name, to_token_name):
        token_pair_with_pool_address = {
            ('ETH', 'USDC'): MAVERICK_CONTRACTS['pool_eth_usdc'],
            ('USDC', 'ETH'): MAVERICK_CONTRACTS['pool_eth_usdc'],
            # ('ETH', 'MAV'): MAVERICK_CONTRACTS['pool_eth_mav'],
            # ('MAV', 'ETH'): MAVERICK_CONTRACTS['pool_eth_mav'],
            ('BUSD', 'ETH'): MAVERICK_CONTRACTS['pool_busd_eth'],
            ('ETH', 'BUSD'): MAVERICK_CONTRACTS['pool_busd_eth'],
            ('BUSD', 'USDC'): MAVERICK_CONTRACTS['pool_busd_usdc'],
            ('USDC', 'BUSD'): MAVERICK_CONTRACTS['pool_busd_usdc'],
            # ('USDC', 'MAV'): MAVERICK_CONTRACTS['pool_usdc_mav'],
            # ('MAV', 'USDC'): MAVERICK_CONTRACTS['pool_usdc_mav'],
            # ('BUSD', 'MAV'): MAVERICK_CONTRACTS['pool_busd_mav'],
            # ('MAV', 'BUSD'): MAVERICK_CONTRACTS['pool_busd_mav']
        }

        return token_pair_with_pool_address[from_token_name, to_token_name]

    @repeater
    @gas_checker
    async def swap(self):

        from_token_name, to_token_name, amount, amount_in_wei = await self.client.get_auto_amount()

        self.client.logger.info(f'{self.client.info} Swap on Maverick: {amount} {from_token_name} -> {to_token_name}')

        from_token_address, to_token_address = ZKSYNC_TOKENS[from_token_name], ZKSYNC_TOKENS[to_token_name]

        if from_token_name != 'ETH':
            await self.client.check_for_approved(from_token_address, MAVERICK_CONTRACTS['router'], amount_in_wei)

        tx_params = await self.client.prepare_transaction(value=amount_in_wei if from_token_name == 'ETH' else 0)
        pool_address = self.get_pool_address(from_token_name, to_token_name)
        deadline = int(time()) + 1800
        min_amount_out = await self.get_min_amount_out(pool_address, from_token_name, amount_in_wei)

        tx_data = self.router_contract.encodeABI(
            fn_name='exactInput',
            args=[(
                self.get_path(from_token_address, pool_address, to_token_address),
                self.client.address if to_token_name != 'ETH' else ZERO_ADDRESS,
                deadline,
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
                    self.client.address
                ] if from_token_name != 'ETH' else None
            )
            full_data.append(tx_additional_data)

        transaction = await self.router_contract.functions.multicall(
            full_data
        ).build_transaction(tx_params)

        tx_hash = await self.client.send_transaction(transaction)

        await self.client.verify_transaction(tx_hash)

    @repeater
    @gas_checker
    async def add_liquidity(self):

        amount_from_settings, amount_from_settings_in_wei = await self.client.check_and_get_eth_for_liquidity()

        self.client.logger.info(f'{self.client.info} Add liquidity to Maverick USDC/ETH pool: {amount_from_settings} ETH')

        tx_params = await self.client.prepare_transaction(value=amount_from_settings_in_wei)

        deadline = int(time()) + 1800
        delta_b = amount_from_settings_in_wei - 100000001
        amount_eth_min = int(amount_from_settings_in_wei * 0.9804)
        position_id = await self.position_contract.functions.tokenOfOwnerByIndex(self.client.address, 0).call()
        pool_contact = self.client.get_contract(MAVERICK_CONTRACTS['pool_eth_usdc'], MAVERICK_POOL_ABI)
        pos = (await pool_contact.functions.getState().call())[0] + 1

        data_params = [
            2,
            pos,
            False,
            0,
            delta_b
        ]

        tx_data = self.router_contract.encodeABI(
            fn_name='addLiquidityToPool',
            args=[
                MAVERICK_CONTRACTS['pool_eth_usdc'],
                position_id,
                [data_params],
                0,
                amount_eth_min,
                deadline
            ]
        )

        tx_additional_data = self.router_contract.encodeABI(
            fn_name='refundETH'
        )

        transaction = await self.router_contract.functions.multicall(
            [tx_data, tx_additional_data]
        ).build_transaction(tx_params)

        tx_hash = await self.client.send_transaction(transaction)

        await self.client.verify_transaction(tx_hash)

    @repeater
    @gas_checker
    async def withdraw_liquidity(self):
        self.client.logger.info(f'{self.client.info} Withdraw liquidity from Maverick')

        _, liquidity_balance = await self.position_inspector_contract.functions.addressBinReservesAllKindsAllTokenIds(
            self.client.address,
            MAVERICK_CONTRACTS['pool_eth_usdc']
        ).call()

        if liquidity_balance != 0:

            tx_params = await self.client.prepare_transaction()
            min_amount_eth_out = int(liquidity_balance * 0.98)
            deadline = int(time()) + 1800
            position_id = await self.position_contract.functions.tokenOfOwnerByIndex(self.client.address, 0).call()

            bin_ids = await self.position_inspector_contract.functions.getTokenBinIds(
                position_id,
                MAVERICK_CONTRACTS['pool_eth_usdc'],
                0,
                1000000
            ).call()

            bin_positions = list(map(lambda bin_id: [bin_id, 2 ** 128 - 1], bin_ids))

            if not await self.position_contract.functions.getApproved(position_id).call():
                tx_approve_position_id = self.position_contract.functions.approve(
                    MAVERICK_CONTRACTS['router'],
                    position_id
                ).build_transaction(self.client.prepare_transaction())

                await self.client.send_transaction(tx_approve_position_id)

            tx_bin_ids_data = self.router_contract.encodeABI(
                fn_name='migrateBinsUpStack',
                args=[
                    MAVERICK_CONTRACTS['pool_eth_usdc'],
                    bin_ids,
                    0,
                    deadline
                ]
            )

            tx_data = self.router_contract.encodeABI(
                fn_name='removeLiquidity',
                args=[
                    MAVERICK_CONTRACTS['pool_eth_usdc'],
                    ZERO_ADDRESS,
                    position_id,
                    bin_positions,
                    0,
                    min_amount_eth_out,
                    deadline
                ]
            )

            tx_additional_data = self.router_contract.encodeABI(
                fn_name='unwrapWETH9',
                args=[
                    min_amount_eth_out,
                    self.client.address
                ]
            )
            tx_sweep_data = self.router_contract.encodeABI(
                fn_name='sweepToken',
                args=[
                    ZKSYNC_TOKENS['USDC'],
                    0,
                    self.client.address
                ]
            )

            transaction = await self.router_contract.functions.multicall(
                [tx_bin_ids_data, tx_data, tx_additional_data, tx_sweep_data]
            ).build_transaction(tx_params)

            tx_hash = await self.client.send_transaction(transaction)

            await self.client.verify_transaction(tx_hash)

        else:
            raise RuntimeError('Insufficient balance on Maverick!')
