from time import time
from modules import DEX, Logger
from modules.interfaces import SoftwareException
from utils.tools import gas_checker, helper
from general_settings import SLIPPAGE
from config import (
    ZERO_ADDRESS,
    MAVERICK_ROUTER_ABI,
    MAVERICK_POOL_INFORMATION_ABI,
    MAVERICK_POSITION_ABI,
    MAVERICK_POSITION_INSPECTOR_ABI,
    MAVERICK_POOL_ABI,
    MAVERICK_CONTRACTS,
    TOKENS_PER_CHAIN
)


class Maverick(DEX, Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)
        self.network = self.client.network.name
        self.router_contract = self.client.get_contract(
            MAVERICK_CONTRACTS[self.network]['router'],
            MAVERICK_ROUTER_ABI
        )
        self.pool_info_contract = self.client.get_contract(
            MAVERICK_CONTRACTS[self.network]['pool_information'],
            MAVERICK_POOL_INFORMATION_ABI
        )
        self.position_contract = self.client.get_contract(
            MAVERICK_CONTRACTS[self.network]['position'],
            MAVERICK_POSITION_ABI
        )
        self.position_inspector_contract = self.client.get_contract(
            MAVERICK_CONTRACTS[self.network]['position_inspector'],
            MAVERICK_POSITION_INSPECTOR_ABI
        )

    async def get_min_amount_out(self, path:bytes, amount_in_wei: int):
        min_amount_out = await self.pool_info_contract.functions.calculateMultihopSwap(
            path,
            amount_in_wei,
            True,
        ).call()

        return int(min_amount_out - (min_amount_out / 100 * SLIPPAGE))

    @staticmethod
    def get_path(from_token_address: str, pool_address:str, to_token_address: str):
        path_data = [from_token_address, pool_address, to_token_address]
        return b"".join((bytes.fromhex(address[2:]) for address in path_data))

    def get_pool_address(self, from_token_name, to_token_name):
        pool_address = MAVERICK_CONTRACTS[self.network].get(f"{from_token_name}-{to_token_name}")
        if pool_address is None:
            pool_address = MAVERICK_CONTRACTS[self.network].get(f"{to_token_name}-{from_token_name}")
        if pool_address is None:
            raise SoftwareException('Maverick does not support this pool')
        return pool_address

    @helper
    @gas_checker
    async def swap(self):
        from_token_name, to_token_name, amount, amount_in_wei = await self.client.get_auto_amount(class_name='Maverick')

        self.logger_msg(*self.client.acc_info, msg=f'Swap on Maverick: {amount} {from_token_name} -> {to_token_name}')

        from_token_address, to_token_address = (TOKENS_PER_CHAIN[self.network][from_token_name],
                                                TOKENS_PER_CHAIN[self.network][to_token_name])

        pool_address = self.get_pool_address(from_token_name, to_token_name)
        deadline = int(time()) + 1800
        path = self.get_path(from_token_address, pool_address, to_token_address)
        min_amount_out = await self.get_min_amount_out(path, amount_in_wei)
        await self.client.price_impact_defender(from_token_name, amount, to_token_name, min_amount_out)

        if from_token_name != 'ETH':
            await self.client.check_for_approved(
                from_token_address, MAVERICK_CONTRACTS[self.network]['router'], amount_in_wei
            )

        tx_data = self.router_contract.encodeABI(
            fn_name='exactInput',
            args=[(
                path,
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

        tx_params = await self.client.prepare_transaction(value=amount_in_wei if from_token_name == 'ETH' else 0)
        transaction = await self.router_contract.functions.multicall(
            full_data
        ).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)

    @helper
    @gas_checker
    async def add_liquidity(self):
        amount, amount_in_wei = await self.client.check_and_get_eth()

        self.logger_msg(
            *self.client.acc_info, msg=f'Add liquidity to Maverick USDC/ETH pool: {amount} ETH')

        deadline = int(time()) + 1800
        delta_b = amount_in_wei - 100000001
        amount_eth_min = int(amount_in_wei * 0.9804)
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

        tx_params = await self.client.prepare_transaction(value=amount_in_wei)
        transaction = await self.router_contract.functions.multicall(
            [tx_data, tx_additional_data]
        ).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)

    @helper
    @gas_checker
    async def withdraw_liquidity(self):
        self.logger_msg(*self.client.acc_info, msg=f'Withdraw liquidity from Maverick')

        _, liquidity_balance = await self.position_inspector_contract.functions.addressBinReservesAllKindsAllTokenIds(
            self.client.address,
            MAVERICK_CONTRACTS['pool_eth_usdc']
        ).call()

        if liquidity_balance != 0:

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
                    TOKENS_PER_CHAIN[self.client.network.name]['USDC'],
                    0,
                    self.client.address
                ]
            )

            tx_params = await self.client.prepare_transaction()
            transaction = await self.router_contract.functions.multicall(
                [tx_bin_ids_data, tx_data, tx_additional_data, tx_sweep_data]
            ).build_transaction(tx_params)

            return await self.client.send_transaction(transaction)

        else:
            raise SoftwareException('Insufficient balance on Maverick!')
