import asyncio
import copy
import random
import traceback
import aiohttp.client_exceptions
import python_socks

from modules import Logger, RequestClient, Client
from general_settings import AMOUNT_PERCENT_WRAPS, VOLUME_MODE
from modules.interfaces import SoftwareException, SoftwareExceptionWithoutRetry, CriticalException, \
    SoftwareExceptionHandled
from utils.tools import helper, gas_checker, sleep
from config import (
    TOKENS_PER_CHAIN, OMNICHAIN_WRAPED_NETWORKS, OMNICHAIN_NETWORKS_DATA,
    TOKENS_PER_CHAIN2, CHAIN_NAME, OKX_NETWORKS_NAME, BINGX_NETWORKS_NAME, BINANCE_NETWORKS_NAME, CEX_WRAPPED_ID,
    COINGECKO_TOKEN_API_NAMES, BITGET_NETWORKS_NAME
)
from settings import (
    CEX_BALANCER_CONFIG, STARGATE_CHAINS, STARGATE_TOKENS, L2PASS_ATTACK_NFT, ZERIUS_ATTACK_NFT,
    SHUFFLE_ATTACK, COREDAO_CHAINS, COREDAO_TOKENS, OKX_WITHDRAW_DATA, BINANCE_DEPOSIT_DATA,
    BINGX_WITHDRAW_DATA, SHUFFLE_NFT_ATTACK, BINANCE_WITHDRAW_DATA, ALL_DST_CHAINS,
    RHINO_CHAIN_ID_FROM, LAYERSWAP_CHAIN_ID_FROM, ORBITER_CHAIN_ID_FROM,
    ACROSS_CHAIN_ID_FROM, WHALE_ATTACK_NFT, RELAY_CHAIN_ID_FROM, SRC_CHAIN_MERKLY,
    SRC_CHAIN_L2PASS, SRC_CHAIN_ZERIUS, DST_CHAIN_MERKLY_REFUEL, DST_CHAIN_L2PASS_REFUEL, DST_CHAIN_ZERIUS_REFUEL,
    SRC_CHAIN_WHALE, DST_CHAIN_WHALE_REFUEL, DST_CHAIN_MERKLY_NFT, DST_CHAIN_L2PASS_NFT, DST_CHAIN_ZERIUS_NFT,
    DST_CHAIN_WHALE_NFT, MERKLY_ATTACK_NFT, L2PASS_ATTACK_REFUEL, MERKLY_ATTACK_REFUEL, WHALE_ATTACK_REFUEL,
    ZERIUS_ATTACK_REFUEL, L0_SEARCH_DATA, OWLTO_CHAIN_ID_FROM, ACROSS_TOKEN_NAME, ORBITER_TOKEN_NAME, OWLTO_TOKEN_NAME,
    LAYERSWAP_TOKEN_NAME, RELAY_TOKEN_NAME, RHINO_TOKEN_NAME, OKX_DEPOSIT_DATA, BINGX_DEPOSIT_DATA,
    SRC_CHAIN_MERKLY_HYPERLANE, DST_CHAIN_MERKLY_HYPERLANE, HYPERLANE_TOKENS_AMOUNT, BUNGEE_CHAIN_ID_FROM,
    BUNGEE_TOKEN_NAME, L0_BRIDGE_COUNT, CUSTOM_SWAP_DATA, BITGET_DEPOSIT_DATA, BITGET_WITHDRAW_DATA, STG_STAKE_CONFIG,
    NITRO_CHAIN_ID_FROM, NITRO_TOKEN_NAME, STARGATE_DUST_CONFIG, STARGATE_AMOUNT, COREDAO_AMOUNT, ACROSS_AMOUNT_LIMITER,
    BUNGEE_AMOUNT_LIMITER, LAYERSWAP_AMOUNT_LIMITER, NITRO_AMOUNT_LIMITER, ORBITER_AMOUNT_LIMITER, OWLTO_AMOUNT_LIMITER,
    RELAY_AMOUNT_LIMITER, RHINO_AMOUNT_LIMITER, BRIDGE_SWITCH_CONTROL, SRC_CHAIN_NOGEM, DST_CHAIN_NOGEM_REFUEL,
    DST_CHAIN_NOGEM_NFT, NOGEM_ATTACK_REFUEL, NOGEM_ATTACK_NFT, NATIVE_CHAIN_ID_FROM, NATIVE_TOKEN_NAME,
    NATIVE_AMOUNT_LIMITER
)


class Custom(Logger, RequestClient):
    def __init__(self, client: Client):
        self.client = client
        Logger.__init__(self)
        RequestClient.__init__(self, client)

    async def collect_eth_util(self):
        from functions import (
            swap_odos, swap_oneinch, swap_izumi, swap_syncswap, swap_bladeswap, unwrap_eth, swap_ambient
        )

        self.logger_msg(*self.client.acc_info, msg=f"Started collecting tokens in ETH")

        func = {
            'Arbitrum': [swap_odos, swap_oneinch],
            'Optimism': [swap_odos, swap_oneinch],
            'Base': [swap_izumi, swap_odos, swap_oneinch],
            'Blast': [swap_bladeswap],
            'Linea': [swap_izumi, swap_syncswap],
            'Scroll': [swap_izumi, swap_ambient],
            'zkSync': [swap_izumi, swap_syncswap, swap_oneinch]
        }[self.client.network.name]

        wallet_balance = {k: await self.client.get_token_balance(k, False)
                          for k, v in TOKENS_PER_CHAIN[self.client.network.name].items()}
        valid_wallet_balance = {k: v[1] for k, v in wallet_balance.items() if v[0] != 0}
        eth_price = await self.client.get_token_price('ethereum')

        for token in ['ETH', 'WETH']:
            if token in valid_wallet_balance:
                valid_wallet_balance[token] *= eth_price

        if valid_wallet_balance['ETH'] < 0.5:
            self.logger_msg(*self.client.acc_info, msg=f'Account has not enough ETH for swap fee', type_msg='warning')
            return True

        if len(valid_wallet_balance.values()) > 1:
            try:
                for token_name, token_balance in valid_wallet_balance.items():
                    if token_name != 'ETH':
                        amount_in_wei = wallet_balance[token_name][0]
                        amount = float(f"{(amount_in_wei / 10 ** await self.client.get_decimals(token_name)):.6f}")
                        amount_in_usd = valid_wallet_balance[token_name]
                        if amount_in_usd > 1:
                            from_token_name, to_token_name = token_name, 'ETH'
                            data = from_token_name, to_token_name, amount, amount_in_wei
                            counter = 0
                            while True:
                                result = False
                                if from_token_name == 'WETH':
                                    module_func = unwrap_eth
                                    data = amount_in_wei
                                else:
                                    module_func = random.choice(func)
                                try:
                                    self.logger_msg(
                                        *self.client.acc_info, msg=f'Launching swap module', type_msg='warning'
                                    )
                                    result = await module_func(
                                        self.client.account_name, self.client.private_key, self.client.network,
                                        self.client.proxy_init, swapdata=data
                                    )
                                    if not result:
                                        counter += 1
                                except Exception as error:
                                    self.logger_msg(
                                        *self.client.acc_info, msg=f'Error in collector: {error}', type_msg='warning'
                                    )
                                    counter += 1
                                    pass
                                if result or counter == 3:
                                    break
                        else:
                            self.logger_msg(*self.client.acc_info, msg=f"{token_name} balance < 1$")
                    await sleep(self, 10, 50)
            except Exception as error:
                self.logger_msg(*self.client.acc_info, msg=f"Error in collector route. Error: {error}")
        else:
            self.logger_msg(*self.client.acc_info, msg=f"Account balance already in ETH!", type_msg='warning')

    @helper
    async def collect_eth(self):
        await self.collect_eth_util()

        return True

    @helper
    async def balance_average(self):
        from functions import okx_withdraw_util, bingx_withdraw_util, binance_withdraw_util, bitget_withdraw_util

        self.logger_msg(*self.client.acc_info, msg=f"Start checking all balances to make it average")

        balancer_data_copy = copy.deepcopy(CEX_BALANCER_CONFIG)

        count = 0
        client = None
        for data in balancer_data_copy:
            while True:
                try:
                    cex_network, wanted_balance, cex_wanted = data
                    if isinstance(cex_network, (tuple, list)):
                        cex_wanted = random.choice(cex_wanted)

                    func, cex_config = {
                        1: (okx_withdraw_util, OKX_NETWORKS_NAME),
                        2: (bingx_withdraw_util, BINGX_NETWORKS_NAME),
                        3: (binance_withdraw_util, BINGX_NETWORKS_NAME),
                        4: (bitget_withdraw_util, BITGET_NETWORKS_NAME),
                    }[cex_wanted]

                    dapp_tokens = [f"{cex_config[cex_network].split('-')[0]}{'.e' if cex_network in [29, 30] else ''}"]
                    dapp_chains = [CEX_WRAPPED_ID[cex_network]]

                    client, index, balance, balance_in_wei, balance_data = await self.balance_searcher(
                        chains=dapp_chains, tokens=dapp_tokens, omni_check=False, silent_mode=True, balancer_mode=True
                    )

                    dep_token = dapp_tokens[index]
                    balance_in_usd, token_price = balance_data
                    wanted_amount_in_usd = float(f'{wanted_balance * token_price:.2f}')

                    if wanted_amount_in_usd > balance_in_usd:
                        need_to_withdraw = float(f"{(wanted_amount_in_usd - balance_in_usd) / token_price:.6f}")

                        if need_to_withdraw * token_price < 1:
                            self.logger_msg(
                                *self.client.acc_info,
                                msg=f"Amount lower than 1$, will set 1$ to withdraw", type_msg='warning'
                            )
                            need_to_withdraw = round(random.uniform(1.0, 1.1) / token_price, 6)
                        else:
                            self.logger_msg(
                                *self.client.acc_info,
                                msg=f"Not enough balance on account in {client.network.name}, launch CEX withdraw module"
                            )

                        await func(client, withdraw_data=(cex_network, (need_to_withdraw, need_to_withdraw)))
                    else:
                        self.logger_msg(
                            *self.client.acc_info,
                            msg=f"Account have enough {dep_token} balance in {client.network.name}", type_msg='success'
                        )
                    await asyncio.sleep(10)
                    break
                except Exception as error:
                    count += 1
                    if count == 3:
                        raise SoftwareException(f"Exception: {error}")
                    self.logger_msg(*self.client.acc_info, msg=f"Exception: {error}", type_msg='error')
                finally:
                    if client:
                        await client.session.close()
        return True
        # else:
        #     fee = random.uniform(0.5, 1)
        #     need_to_deposit = float(f"{(sum_balance_in_usd - wanted_amount_in_usd) / eth_price - fee:.6f}")
        #
        #     self.logger_msg(*self.client.acc_info, msg=f"ETH balance on account is too much, launch OKX deposit module")
        #
        #     return await okx_deposit_util(self.client, deposit_data=(okx_network, need_to_deposit))

    @helper
    async def wraps_abuser(self):
        from functions import swap_odos, swap_oneinch, swap_xyfinance

        func = {
            'Base': [swap_odos, swap_oneinch],
            'Linea': [swap_xyfinance],
            'Scroll': [swap_xyfinance],
            'zkSync': [swap_odos, swap_oneinch]
        }[self.client.network.name]

        current_tokens = list(TOKENS_PER_CHAIN[self.client.network.name].items())[:2]

        wrapper_counter = 0
        for _ in range(2):
            wallet_balance = {k: await self.client.get_token_balance(k, False) for k, v in current_tokens}
            valid_wallet_balance = {k: v[1] for k, v in wallet_balance.items() if v[0] != 0}
            eth_price = await self.client.get_token_price('ethereum')

            if 'ETH' in valid_wallet_balance:
                valid_wallet_balance['ETH'] = valid_wallet_balance['ETH'] * eth_price

            if 'WETH' in valid_wallet_balance:
                valid_wallet_balance['WETH'] = valid_wallet_balance['WETH'] * eth_price

            max_token = max(valid_wallet_balance, key=lambda x: valid_wallet_balance[x])

            if max_token == 'ETH' and wrapper_counter == 1:
                continue
            elif max_token == 'WETH' and wrapper_counter == 1:
                self.logger_msg(*self.client.acc_info, msg=f"Current balance in WETH, running unwrap")

            percent = round(random.uniform(*AMOUNT_PERCENT_WRAPS), 9) / 100 if max_token == 'ETH' else 1
            amount_in_wei = int(wallet_balance[max_token][0] * percent)
            amount = self.client.custom_round(amount_in_wei / 10 ** 18, 6)

            if max_token == 'ETH':
                msg = f'Wrap {amount:.6f} ETH'
                from_token_name, to_token_name = 'ETH', 'WETH'
            else:
                msg = f'Unwrap {amount:.6f} WETH'
                from_token_name, to_token_name = 'WETH', 'ETH'

            self.logger_msg(*self.client.acc_info, msg=msg)

            if (max_token == 'ETH' and valid_wallet_balance[max_token] > 1
                    or max_token == 'WETH' and valid_wallet_balance[max_token] != 0):
                data = from_token_name, to_token_name, amount, amount_in_wei
                counter = 0
                result = False
                while True:
                    module_func = random.choice(func)
                    try:
                        result = await module_func(self.client.account_name, self.client.private_key,
                                                   self.client.network, self.client.proxy_init, swapdata=data)
                        wrapper_counter += 1
                    except:
                        pass
                    if result or counter == 3:
                        break

            else:
                self.logger_msg(*self.client.acc_info, msg=f"{from_token_name} balance is too low (lower 1$)")

        return True

    @helper
    async def swaps_abuser(self):
        from functions import swap_odos, swap_oneinch, swap_xyfinance

        func = {
            'Base': [swap_odos, swap_oneinch],
            'Linea': [swap_xyfinance],
            'Scroll': [swap_xyfinance],
            'zkSync': [swap_odos, swap_oneinch]
        }[self.client.network.name]

        current_tokens = list(TOKENS_PER_CHAIN[self.client.network.name].items())[:2]

        wrapper_counter = 0
        for _ in range(2):
            wallet_balance = {k: await self.client.get_token_balance(k, False) for k, v in current_tokens}
            valid_wallet_balance = {k: v[1] for k, v in wallet_balance.items() if v[0] != 0}
            eth_price = await self.client.get_token_price('ethereum')

            if 'ETH' in valid_wallet_balance:
                valid_wallet_balance['ETH'] = valid_wallet_balance['ETH'] * eth_price

            if 'WETH' in valid_wallet_balance:
                valid_wallet_balance['WETH'] = valid_wallet_balance['WETH'] * eth_price

            max_token = max(valid_wallet_balance, key=lambda x: valid_wallet_balance[x])

            if max_token == 'ETH' and wrapper_counter == 1:
                continue
            elif max_token == 'WETH' and wrapper_counter == 1:
                self.logger_msg(*self.client.acc_info, msg=f"Current balance in WETH, running unwrap")

            percent = round(random.uniform(*AMOUNT_PERCENT_WRAPS), 9) / 100 if max_token == 'ETH' else 1
            amount_in_wei = int(wallet_balance[max_token][0] * percent)
            amount = self.client.custom_round(amount_in_wei / 10 ** 18, 6)

            if max_token == 'ETH':
                msg = f'Wrap {amount:.6f} ETH'
                from_token_name, to_token_name = 'ETH', 'WETH'
            else:
                msg = f'Unwrap {amount:.6f} WETH'
                from_token_name, to_token_name = 'WETH', 'ETH'

            self.logger_msg(*self.client.acc_info, msg=msg)

            if (max_token == 'ETH' and valid_wallet_balance[max_token] > 1
                    or max_token == 'WETH' and valid_wallet_balance[max_token] != 0):
                data = from_token_name, to_token_name, amount, amount_in_wei
                counter = 0
                result = False
                while True:
                    module_func = random.choice(func)
                    try:
                        result = await module_func(self.client.account_name, self.client.private_key,
                                                   self.client.network, self.client.proxy_init, swapdata=data)
                        wrapper_counter += 1
                    except:
                        pass
                    if result or counter == 3:
                        break

            else:
                self.logger_msg(*self.client.acc_info, msg=f"{from_token_name} balance is too low (lower 1$)")

        return True

    @helper
    async def smart_bridge_l0(self, dapp_id: int = None, dust_mode: bool = False):
        from functions import Stargate, CoreDAO

        class_name, tokens, chains, amounts = {
            1: (Stargate, STARGATE_TOKENS, STARGATE_CHAINS, STARGATE_AMOUNT),
            2: (CoreDAO, COREDAO_TOKENS, COREDAO_CHAINS, COREDAO_AMOUNT)
        }[dapp_id]

        if dust_mode:
            tokens, chains = STARGATE_DUST_CONFIG

        converted_chains = copy.deepcopy(chains)
        if any([isinstance(item, tuple) for item in chains]):
            new_chains = []
            for item in chains:
                if isinstance(item, tuple):
                    new_chains.extend(item)
                else:
                    new_chains.append(item)
            converted_chains = new_chains

        start_chain = None
        used_chains = []
        result_list = []
        count_copy = copy.deepcopy(L0_BRIDGE_COUNT)
        total_bridge_count = random.choice(count_copy) if isinstance(count_copy, list) else count_copy
        for bridge_count in range(total_bridge_count):
            while True:
                try:
                    current_client, index, balance, balance_in_wei, balances_in_usd = await self.balance_searcher(
                        converted_chains, tokens, omni_check=True
                    )

                    from_token_name = tokens[index]

                    if dapp_id == 1:

                        if any([isinstance(path, tuple) for path in chains]):
                            tuple_chains = chains[-1]
                            if not isinstance(tuple_chains, tuple) and not all(
                                    isinstance(chain, int) for chain in chains[0: -1]
                            ) and len(chains) != 2:
                                setting_format = '[chain, chain, ..., (chain, chain, ...)]'
                                raise SoftwareExceptionWithoutRetry(
                                    f'This mode on Stargate Bridges support only {setting_format} format'
                                )

                            if bridge_count + 1 == total_bridge_count:
                                final_chains = [chain for chain in chains if isinstance(chain, int)]
                                available_chains = [
                                    chain for chain in final_chains if chain != converted_chains[index]
                                ]
                                dst_chain = random.choice(available_chains)
                            elif bridge_count + 1 == 1:
                                dst_chain = tuple_chains[0]
                            else:
                                available_tuple_chains = [
                                    chain for chain in tuple_chains if chain != converted_chains[index]
                                ]
                                dst_chain = random.choice(available_tuple_chains)
                        elif isinstance(chains, tuple):
                            if total_bridge_count != len(chains) - 1:
                                raise SoftwareExceptionWithoutRetry('L0_BRIDGE_COUNT != all chains in params - 1')
                            dst_chain = converted_chains[bridge_count + 1]
                        else:
                            if not start_chain:
                                start_chain = converted_chains[index]
                            used_chains.append(start_chain)

                            if len(used_chains) >= len(chains):
                                dst_chain = random.choice(
                                    [chain for chain in converted_chains if chain != converted_chains[index]])
                            else:
                                available_chains = [chain for chain in converted_chains if chain not in used_chains]
                                dst_chain = random.choice(available_chains)

                            used_chains.append(dst_chain)

                    else:
                        if isinstance(chains, tuple):
                            if total_bridge_count != len(chains) - 1:
                                raise SoftwareExceptionWithoutRetry('L0_BRIDGE_COUNT != all chains in params - 1')
                            dst_chain = converted_chains[bridge_count + 1]
                        elif converted_chains[index] == 11:
                            if len(converted_chains) == 2:
                                dst_chain = random.choice([chain for chain in converted_chains if chain != 11])
                            elif len(converted_chains) == 3:
                                if 11 in [converted_chains[0], converted_chains[-1]] and converted_chains[1] != 11:
                                    raise SoftwareExceptionWithoutRetry(
                                        'This mode on CoreDAO bridges support only "[chain, 11(CoreDAO), chain]" format')
                                dst_chain = converted_chains[-1]
                                if len(used_chains) == 3:
                                    dst_chain = converted_chains[0]
                                    used_chains = []
                            else:
                                raise SoftwareExceptionWithoutRetry(
                                    'CoreDAO bridges support only 2 or 3 chains in list')
                        else:
                            dst_chain = 11

                        used_chains.append(dst_chain)

                    src_chain_name = current_client.network.name
                    dst_chain_name, dst_chain_id, _, _ = OMNICHAIN_NETWORKS_DATA[dst_chain]
                    to_token_name = tokens[converted_chains.index(dst_chain)]

                    if src_chain_name == dst_chain_name:
                        raise SoftwareException(
                            f'Can`t bridge into same network: SRC Chain:{src_chain_name}, DST Chain:{dst_chain_name}'
                        )

                    if from_token_name != 'ETH':
                        contract = current_client.get_contract(
                            TOKENS_PER_CHAIN2[current_client.network.name][from_token_name])
                        decimals = await contract.functions.decimals().call()
                    else:
                        decimals = 18

                    amount_in_wei = self.client.to_wei((
                        await current_client.get_smart_amount(amounts, token_name=tokens[index], omnicheck=True)
                    ), decimals)

                    if dust_mode:
                        amount_in_wei = int(amount_in_wei * random.uniform(0.0000001, 0.0000003))

                    amount = f"{amount_in_wei / 10 ** decimals:.4f}"

                    swapdata = (src_chain_name, dst_chain_name, dst_chain_id,
                                from_token_name, to_token_name, amount, amount_in_wei)

                    result_list.append(await class_name(current_client).bridge(swapdata=swapdata))

                    if current_client:
                        await current_client.session.close()

                    if total_bridge_count != 1:
                        await sleep(self)

                    break

                except Exception as error:
                    self.logger_msg(
                        *self.client.acc_info,
                        msg=f"Error during the route. Will try again in 1 min... Error: {error}", type_msg='warning'
                    )
                    await asyncio.sleep(60)

        if total_bridge_count != 1:
            return all(result_list)
        return any(result_list)

    @helper
    async def swap_bridged_usdc(self):
        from functions import swap_uniswap

        amount_in_wei, amount, _ = await self.client.get_token_balance('USDC.e')
        data = 'USDC.e', 'USDC', amount, amount_in_wei

        if amount_in_wei == 0:
            raise SoftwareException("Insufficient USDC balances")

        return await swap_uniswap(self.client.account_name, self.client.private_key,
                                  self.client.network, self.client.proxy_init, swapdata=data)

    @helper
    @gas_checker
    async def custom_swap(self):
        from functions import swap_oneinch, swap_izumi, swap_syncswap, swap_odos, swap_sushiswap

        from_token_name, to_token_name, amount_tuple, networks = CUSTOM_SWAP_DATA

        if isinstance(to_token_name, (list, tuple)):
            to_token_name = random.choice(to_token_name)

        if isinstance(from_token_name, (list, tuple)):
            from_token_name = random.choice(from_token_name)

        if isinstance(networks, (list, tuple)):
            chains = networks
            tokens = [from_token_name for _ in range(len(chains))]

            current_client, index, balance, balance_in_wei, balances_in_usd = await self.balance_searcher(
                chains, tokens
            )
        else:
            current_client = await self.client.new_client(OMNICHAIN_WRAPED_NETWORKS[networks])

        funcs = {
            'Arbitrum': [swap_oneinch, swap_odos],
            'Arbitrum Nova': [swap_sushiswap],
            'Base': [swap_odos, swap_oneinch],
            'Linea': [swap_izumi, swap_syncswap],
            'Scroll': [swap_izumi, swap_syncswap],
            'zkSync': [swap_izumi, swap_syncswap],
            'Optimism': [swap_oneinch, swap_odos],
            # 'Polygon ZKEVM': [swap_xyfinance],
            'BNB Chain': [swap_oneinch],
            # 'Manta': [swap_xyfinance],
            'Polygon': [swap_oneinch],
            # 'Zora': [swap_oneinch],
        }[current_client.network.name]

        swap_module = random.choice(funcs)
        amount = await current_client.get_smart_amount(amount_tuple, token_name=from_token_name)

        if amount == 0:
            raise SoftwareException(f"Insufficient {from_token_name} balances")

        decimals = await current_client.get_decimals(from_token_name)
        amount_in_wei = current_client.to_wei(amount, decimals)
        data = from_token_name, to_token_name, amount, amount_in_wei

        return await swap_module(current_client.account_name, current_client.private_key, current_client.network,
                                 current_client.proxy_init, swapdata=data)

    @helper
    @gas_checker
    async def layerzero_attack(self, dapp_id: int = None, dapp_mode: int = None):
        from functions import omnichain_util

        class_id, attack_data = {
            1: (1, (L2PASS_ATTACK_REFUEL, L2PASS_ATTACK_NFT)),
            2: (2, (NOGEM_ATTACK_REFUEL, NOGEM_ATTACK_NFT)),
            3: (3, (MERKLY_ATTACK_REFUEL, MERKLY_ATTACK_NFT)),
            4: (4, (WHALE_ATTACK_REFUEL, WHALE_ATTACK_NFT)),
            5: (5, (ZERIUS_ATTACK_REFUEL, ZERIUS_ATTACK_NFT)),
        }[dapp_id]

        attack_data_without_none = []

        if dapp_mode == 1:
            attack_data = attack_data[0]
            if SHUFFLE_ATTACK:
                random.shuffle(attack_data)
        elif dapp_mode == 2:
            attack_data = attack_data[1]
            if SHUFFLE_NFT_ATTACK:
                random.shuffle(attack_data)

        for path in attack_data:
            if isinstance(path, tuple):
                module = random.choice(path)
                if module:
                    attack_data_without_none.append(module)
                continue
            attack_data_without_none.append(path)

        for attack_info in attack_data_without_none:
            if dapp_mode == 1:
                chain_id_from, chain_to_id, amount = attack_info
                if isinstance(chain_id_from, list):
                    chain_id_from = random.choice(chain_id_from)
                if isinstance(chain_to_id, list):
                    chain_to_id = random.choice(chain_to_id)
                attack_data = {
                    chain_to_id: (amount, self.client.custom_round(amount * 1.1, 7))
                }
            elif dapp_mode == 2:
                chain_id_from, chain_to_id = attack_info
                if isinstance(chain_id_from, list):
                    chain_id_from = random.choice(chain_id_from)
                if isinstance(chain_to_id, list):
                    attack_data = random.choice(chain_to_id)
                else:
                    attack_data = chain_to_id
            else:
                raise SoftwareExceptionWithoutRetry(f'This dapp mode is not exist: {dapp_mode}')

            await omnichain_util(
                self.client.account_name, self.client.private_key, self.client.proxy_init,
                chain_id_from, attack_data=attack_data, dapp_id=class_id, dapp_mode=dapp_mode
            )

            await sleep(self)

        return True

    async def balance_searcher(
            self, chains, tokens=None, omni_check: bool = True, native_check: bool = False, silent_mode: bool = False,
            balancer_mode: bool = False
    ):
        index = 0
        clients = []
        while True:
            try:
                clients = [await self.client.new_client(OMNICHAIN_WRAPED_NETWORKS[chain] if omni_check else chain)
                           for chain in chains]

                if native_check:
                    tokens = [client.token for client in clients]

                balances = [await client.get_token_balance(
                    omnicheck=omni_check if token not in ['USDV', 'STG', 'MAV', 'CORE'] else True, token_name=token,
                )
                            for client, token in zip(clients, tokens)]

                if all(balance_in_wei == 0 for balance_in_wei, _, _ in balances) and not balancer_mode:
                    raise SoftwareException('Insufficient balances in all networks!')

                balances_in_usd = []
                for balance_in_wei, balance, token_name in balances:
                    token_price = 1
                    if 'USD' not in token_name:
                        token_price = await self.client.get_token_price(COINGECKO_TOKEN_API_NAMES[token_name])
                    balance_in_usd = balance * token_price
                    balances_in_usd.append([balance_in_usd, token_price])

                index = balances_in_usd.index(max(balances_in_usd, key=lambda x: x[0]))

                for index_client, client in enumerate(clients):
                    if index_client != index:
                        await client.session.close()

                if not silent_mode:
                    self.logger_msg(
                        *self.client.acc_info,
                        msg=f"Detected {round(balances[index][1], 5)} {tokens[index]} in {clients[index].network.name}",
                        type_msg='success'
                    )

                return clients[index], index, balances[index][1], balances[index][0], balances_in_usd[index]

            except (aiohttp.client_exceptions.ClientProxyConnectionError, asyncio.exceptions.TimeoutError,
                    aiohttp.client_exceptions.ClientHttpProxyError, python_socks.ProxyError):
                self.logger_msg(
                    *self.client.acc_info,
                    msg=f"Connection to RPC is not stable. Will try again in 1 min...",
                    type_msg='warning'
                )
                await asyncio.sleep(60)
            except SoftwareException as error:
                raise error
            except Exception as error:
                traceback.print_exc()
                self.logger_msg(
                    *self.client.acc_info,
                    msg=f"Bad response from RPC. Will try again in 1 min... Error: {error}", type_msg='warning'
                )
                await asyncio.sleep(60)
            finally:
                for index_client, client in enumerate(clients):
                    if index_client != index:
                        await client.session.close()

    @helper
    @gas_checker
    async def smart_stake_stg(self):
        from functions import Stargate
        chains = STARGATE_CHAINS
        tokens = ['STG' for _ in range(len(chains))]
        converted_chains = copy.deepcopy(chains)
        random.shuffle(converted_chains)
        if any([isinstance(item, tuple) for item in chains]):
            new_chains = []
            for item in chains:
                if isinstance(item, tuple):
                    new_chains.extend(item)
                else:
                    new_chains.append(item)
            converted_chains = new_chains

        counter = 0
        while True:

            current_client, index, balance, balance_in_wei, balances_in_usd = await self.balance_searcher(
                converted_chains, tokens, omni_check=True
            )

            amount = await current_client.get_smart_amount(STG_STAKE_CONFIG[1], token_name='STG', omnicheck=True)
            stake_amount = self.client.custom_round(amount, 6)
            stake_amount_in_wei = current_client.to_wei(stake_amount, 18)
            lock_time = int((random.randint(*STG_STAKE_CONFIG[0]) * 30))
            if lock_time == 0:
                raise SoftwareExceptionWithoutRetry('STG_STAKE_CONFIG[0] can`t be zero')
            stakedata = stake_amount, stake_amount_in_wei, lock_time
            try:
                await Stargate(current_client).stake_stg(stakedata=stakedata)
            except Exception as error:
                if 'old tokens' in str(error):
                    counter += 1
                    if counter == len(chains):
                        self.logger_msg(
                            *self.client.acc_info, msg=f"You are already staked STG in all chains", type_msg='warning'
                        )
                        return True

                    self.logger_msg(
                        *self.client.acc_info,
                        msg=f"You are already staked STG in {current_client.network.name}. Trying take next chain...",
                        type_msg='warning'
                    )
                    converted_chains.remove(converted_chains[index])
                else:
                    raise error

    @helper
    @gas_checker
    async def smart_random_approve(self):
        amount = random.uniform(1, 1000)
        while True:
            client = None
            try:
                from config import (IZUMI_CONTRACTS, MAVERICK_CONTRACTS, RANGO_CONTRACTS, ODOS_CONTRACTS,
                                    ONEINCH_CONTRACTS,
                                    OPENOCEAN_CONTRACTS, PANCAKE_CONTRACTS, SUSHISWAP_CONTRACTS,
                                    UNISWAP_CONTRACTS, WOOFI_CONTRACTS, XYFINANCE_CONTRACTS, TOKENS_PER_CHAIN)

                all_contracts = {
                    "Rango.Exchange": RANGO_CONTRACTS,
                    "Maverick": MAVERICK_CONTRACTS,
                    "SushiSwap": SUSHISWAP_CONTRACTS,
                    "Uniswap": UNISWAP_CONTRACTS,
                    "PancakeSwap": PANCAKE_CONTRACTS,
                    "WooFi": WOOFI_CONTRACTS,
                    "iZumi": IZUMI_CONTRACTS,
                    "ODOS": ODOS_CONTRACTS,
                    "1inch": ONEINCH_CONTRACTS,
                    "OpenOcean": OPENOCEAN_CONTRACTS,
                    "XYfinance": XYFINANCE_CONTRACTS,
                }

                chains = {
                    0: STARGATE_CHAINS,
                    1: COREDAO_CHAINS,
                }[L0_SEARCH_DATA]

                converted_chains = copy.deepcopy(chains)
                if any([isinstance(item, tuple) for item in chains]):
                    new_chains = []
                    for item in chains:
                        if isinstance(item, tuple):
                            new_chains.extend(item)
                        else:
                            new_chains.append(item)
                    converted_chains = new_chains

                client, index, _, _, _ = await self.balance_searcher(
                    converted_chains, native_check=True, omni_check=True
                )

                network_name = client.network.name

                all_network_contracts = {
                    name: contracts[network_name]['router']
                    for name, contracts in all_contracts.items()
                    if contracts.get(network_name)
                }

                approve_contracts = [(k, v) for k, v in all_network_contracts.items()]
                contract_name, approve_contract = random.choice(approve_contracts)
                native = [client.network.token, f"W{client.network.token}"]
                token_contract = random.choice(
                    [i for i in list(TOKENS_PER_CHAIN[network_name].items()) if i[0] not in native]
                )
                amount *= 1.1
                amount_in_wei = self.client.to_wei(amount, await client.get_decimals(token_contract[0]))

                message = f"Approve {amount:.4f} {token_contract[0]} for {contract_name}"
                self.logger_msg(*client.acc_info, msg=message)

                result = await client.check_for_approved(
                    token_contract[1], approve_contract, amount_in_wei, without_bal_check=True
                )

                if not result:
                    raise SoftwareException('Bad approve, trying again with higher amount...')
                return result
            finally:
                if client:
                    await client.session.close()

    @helper
    @gas_checker
    async def smart_layerzero_util(self, dapp_id: int = None, dapp_mode: int = None):
        from functions import omnichain_util

        class_id, src_chains, dst_tuple_data = {
            1: (1, SRC_CHAIN_L2PASS, (DST_CHAIN_L2PASS_REFUEL, DST_CHAIN_L2PASS_NFT)),
            2: (2, SRC_CHAIN_NOGEM, (DST_CHAIN_NOGEM_REFUEL, DST_CHAIN_NOGEM_NFT)),
            3: (3, SRC_CHAIN_MERKLY, (DST_CHAIN_MERKLY_REFUEL, DST_CHAIN_MERKLY_NFT)),
            4: (4, SRC_CHAIN_WHALE, (DST_CHAIN_WHALE_REFUEL, DST_CHAIN_WHALE_NFT)),
            5: (5, SRC_CHAIN_ZERIUS, (DST_CHAIN_ZERIUS_REFUEL, DST_CHAIN_ZERIUS_NFT)),
        }[dapp_id]

        dst_datas, module_name = {
            1: (list(dst_tuple_data[0].items()), 'refuel'),
            2: (dst_tuple_data[1], 'bridge NFT')
        }[dapp_mode]

        random.shuffle(src_chains)
        random.shuffle(dst_datas)

        result = False
        action_flag = False
        for dst_data in dst_datas:
            chain_name_to = CHAIN_NAME[OMNICHAIN_WRAPED_NETWORKS[dst_data if dapp_mode == 2 else dst_data[0]]]
            for src_chain in src_chains:
                try:
                    attack_data = {
                        dst_data[0]: dst_data[1]
                    } if dapp_mode == 1 else dst_data

                    action_flag = await omnichain_util(
                        self.client.account_name, self.client.private_key, self.client.proxy_init,
                        chain_from_id=src_chain, dapp_id=class_id, dapp_mode=dapp_mode, attack_data=attack_data,
                        need_check=True
                    )

                    if action_flag:
                        chain_name_from = CHAIN_NAME[OMNICHAIN_WRAPED_NETWORKS[src_chain]]
                        self.logger_msg(
                            *self.client.acc_info,
                            msg=f"Detected funds to {module_name} into {chain_name_to} from {chain_name_from}",
                            type_msg='success')

                        result = await omnichain_util(
                            self.client.account_name, self.client.private_key, self.client.proxy_init,
                            chain_from_id=src_chain, dapp_id=class_id, dapp_mode=dapp_mode, attack_data=attack_data
                        )

                        if not ALL_DST_CHAINS:
                            if result:
                                return True
                            raise SoftwareException(f'Software do not complete {module_name}. Will try again...')

                        if ALL_DST_CHAINS:
                            random.shuffle(src_chains)
                            if result:
                                break

                        await sleep(self)

                except SoftwareException as error:
                    raise error
                except Exception as error:
                    traceback.print_exc()
                    self.logger_msg(
                        *self.client.acc_info,
                        msg=f"Exception during smart {module_name}: {error}", type_msg='warning'
                    )

            if not result:
                self.logger_msg(
                    *self.client.acc_info,
                    msg=f"Can`t {module_name} into {chain_name_to} from those SRC networks\n",
                    type_msg='warning'
                )

        if action_flag is False:
            self.logger_msg(
                *self.client.acc_info, msg=f"Can`t detect funds in all networks!", type_msg='warning')

        if ALL_DST_CHAINS:
            return True
        return result

    @helper
    @gas_checker
    async def merkly_omnichain_util(self, dapp_mode: int, dapp_function: int):
        from functions import omnichain_util

        module_name, src_chains, dst_chains, token_amounts, refuel_data = {
            3: ('Hyperlane', SRC_CHAIN_MERKLY_HYPERLANE, DST_CHAIN_MERKLY_HYPERLANE, HYPERLANE_TOKENS_AMOUNT, 0),
        }[dapp_mode]

        dst_datas, module_func_name = {
            2: (dst_chains, 'bridge NFT'),
            3: (dst_chains, 'bridge Token')
        }[dapp_function]

        random.shuffle(src_chains)
        random.shuffle(dst_datas)
        func_mode = f"{module_func_name} {module_name}"

        result = False
        action_flag = False
        for dst_data in dst_datas:
            chain_name_to = CHAIN_NAME[OMNICHAIN_WRAPED_NETWORKS[dst_data if dapp_function != 1 else dst_data[0]]]
            for src_chain in src_chains:
                try:
                    if dapp_function == 1:
                        attack_data = {
                            dst_data[0]: dst_data[1]
                        }
                    elif dapp_function == 2:
                        attack_data = dst_data
                    else:
                        tokens_amount_mint, tokens_amount_bridge = token_amounts
                        if isinstance(tokens_amount_bridge, tuple):
                            tokens_amount_bridge = random.choice(tokens_amount_bridge)
                        if isinstance(tokens_amount_mint, tuple):
                            tokens_amount_mint = random.choice(tokens_amount_mint)

                        attack_data = tokens_amount_mint, tokens_amount_bridge, dst_data

                    action_flag = await omnichain_util(
                        self.client.account_name, self.client.private_key, self.client.proxy_init,
                        chain_from_id=src_chain, dapp_id=3, dapp_mode=func_mode, attack_data=attack_data,
                        need_check=True
                    )

                    if action_flag:
                        chain_name_from = CHAIN_NAME[OMNICHAIN_WRAPED_NETWORKS[src_chain]]
                        self.logger_msg(
                            *self.client.acc_info,
                            msg=f"Detected funds to {module_func_name} into {chain_name_to} from {chain_name_from}",
                            type_msg='success')

                        result = await omnichain_util(
                            self.client.account_name, self.client.private_key, self.client.proxy_init,
                            chain_from_id=src_chain, dapp_id=3, dapp_mode=func_mode, attack_data=attack_data
                        )

                        if not ALL_DST_CHAINS:
                            if result:
                                return True
                            raise SoftwareException(f'Software do not complete {module_name}. Will try again')

                        if ALL_DST_CHAINS:
                            random.shuffle(src_chains)
                            if result:
                                break

                        await sleep(self)

                except SoftwareException as error:
                    raise error
                except Exception as error:
                    self.logger_msg(
                        *self.client.acc_info,
                        msg=f"Exception during smart {module_func_name}: {error}", type_msg='warning'
                    )

            if not result and ALL_DST_CHAINS:
                self.logger_msg(
                    *self.client.acc_info,
                    msg=f"Can`t {module_func_name} into {chain_name_to} from those SRC networks\n",
                    type_msg='warning'
                )

        if action_flag is False:
            self.logger_msg(
                *self.client.acc_info, msg=f"Can`t detect funds in all networks!", type_msg='warning')

        if ALL_DST_CHAINS:
            return True
        return result

    @helper
    async def smart_cex_withdraw(self, dapp_id: int):
        while True:
            try:
                from functions import okx_withdraw_util, bingx_withdraw_util, binance_withdraw_util, \
                    bitget_withdraw_util

                func, withdraw_data = {
                    1: (okx_withdraw_util, OKX_WITHDRAW_DATA),
                    2: (bingx_withdraw_util, BINGX_WITHDRAW_DATA),
                    3: (binance_withdraw_util, BINANCE_WITHDRAW_DATA),
                    4: (bitget_withdraw_util, BITGET_WITHDRAW_DATA)
                }[dapp_id]

                withdraw_data_copy = copy.deepcopy(withdraw_data)

                random.shuffle(withdraw_data_copy)
                result_list = []

                for index, data in enumerate(withdraw_data_copy, 1):
                    current_data = data
                    if isinstance(data[0], list):
                        current_data = random.choice(data)
                        if not current_data:
                            continue

                    network, amount = current_data

                    if isinstance(amount[0], str):
                        amount = f"{self.client.custom_round(random.uniform(float(amount[0]), float(amount[1])), 6) / 100}"

                    result_list.append(await func(self.client, withdraw_data=(network, amount)))

                    if index != len(withdraw_data_copy):
                        await sleep(self)

                return all(result_list)
            except CriticalException as error:
                raise error
            except Exception as error:
                self.logger_msg(self.client.account_name, None, msg=f'{error}', type_msg='error')
                msg = f"Software cannot continue, awaiting operator's action. Will try again in 1 min..."
                self.logger_msg(self.client.account_name, None, msg=msg, type_msg='warning')
                await asyncio.sleep(60)

    @helper
    @gas_checker
    async def smart_cex_deposit(self, dapp_id: int):
        from functions import cex_deposit_util

        class_id, deposit_data, cex_config = {
            1: (1, OKX_DEPOSIT_DATA, OKX_NETWORKS_NAME),
            2: (2, BINGX_DEPOSIT_DATA, BINGX_NETWORKS_NAME),
            3: (3, BINANCE_DEPOSIT_DATA, BINANCE_NETWORKS_NAME),
            4: (4, BITGET_DEPOSIT_DATA, BITGET_NETWORKS_NAME),
        }[dapp_id]

        deposit_data_copy = copy.deepcopy(deposit_data)

        client = None
        result_list = []
        for data in deposit_data_copy:
            while True:
                try:
                    current_data = data
                    if isinstance(data[0], list):
                        current_data = random.choice(data)
                        if not current_data:
                            continue

                    networks, amount, limit_amount, wanted_to_hold_amount = current_data
                    if (not isinstance(networks, (int, tuple)) or not isinstance(amount, tuple)
                            or not isinstance(limit_amount, (int, float)) or not isinstance(wanted_to_hold_amount,
                                                                                            tuple)):
                        raise CriticalException(
                            'Software only support [1, (1, 1), 0, (1, 1)] deposit format. See CEX CONTROL'
                        )

                    if isinstance(networks, tuple):
                        dapp_tokens = [f"{cex_config[network].split('-')[0]}{'.e' if network in [29, 30] else ''}"
                                       for network in networks]
                        dapp_chains = [CEX_WRAPPED_ID[chain] for chain in networks]
                    else:
                        dapp_tokens = [f"{cex_config[networks].split('-')[0]}{'.e' if networks in [29, 30] else ''}"]
                        dapp_chains = [CEX_WRAPPED_ID[networks]]

                    try:
                        client, chain_index, balance, _, balance_data = await self.balance_searcher(
                            chains=dapp_chains, tokens=dapp_tokens, omni_check=False
                        )
                    except Exception as error:
                        if 'Insufficient balances in all networks!' in str(error):
                            break
                        else:
                            raise error

                    balance_in_usd, token_price = balance_data

                    if balance_in_usd == 0:
                        self.logger_msg(*self.client.acc_info, msg=f'Can`t deposit ZERO amount', type_msg='warning')
                        break

                    dep_token = dapp_tokens[chain_index]
                    omnicheck = True if dep_token in ['USDV', 'STG', 'MAV', 'CORE'] else False

                    dep_network = networks if isinstance(networks, int) else networks[chain_index]
                    min_wanted_amount, max_wanted_amount = min(wanted_to_hold_amount), max(wanted_to_hold_amount)

                    if balance_in_usd >= limit_amount:

                        dep_amount = await client.get_smart_amount(amount, token_name=dep_token, omnicheck=omnicheck)
                        deposit_fee = int(await client.simulate_transfer(token_name=dep_token, omnicheck=omnicheck) * 2)
                        min_hold_balance = random.uniform(min_wanted_amount, max_wanted_amount) / token_price

                        if dep_token == client.token and balance < dep_amount + deposit_fee:
                            dep_amount = dep_amount - deposit_fee

                        if balance - dep_amount < 0:
                            raise SoftwareException('Account balance - deposit fee < 0')

                        if balance - dep_amount < min_hold_balance:
                            need_to_freeze_amount = min_hold_balance - (balance - dep_amount)
                            dep_amount = dep_amount - need_to_freeze_amount

                        if dep_amount < 0:
                            raise CriticalException(
                                f'Set CEX_DEPOSIT_LIMITER[2 value] lower than {wanted_to_hold_amount}. '
                                f'Current amount = {dep_amount:.4f} {dep_token}')

                        dep_amount_in_usd = dep_amount * token_price * 0.99

                        if balance_in_usd >= dep_amount_in_usd:

                            deposit_data = dep_network, self.client.custom_round(dep_amount, 6)

                            if len(deposit_data_copy) == 1:
                                return await cex_deposit_util(client, dapp_id=class_id, deposit_data=deposit_data)
                            else:
                                result_list.append(
                                    await cex_deposit_util(client, dapp_id=class_id, deposit_data=deposit_data)
                                )
                                break

                        info = f"{balance_in_usd:.2f}$ < {dep_amount_in_usd:.2f}$"
                        raise SoftwareExceptionHandled(f'Account {dep_token} balance < wanted deposit amount: {info}')

                    info = f"{balance_in_usd:.2f}$ < {limit_amount:.2f}$"
                    raise SoftwareExceptionHandled(f'Account {dep_token} balance < wanted limit amount: {info}')

                except CriticalException as error:
                    raise error
                except Exception as error:
                    raise error
                finally:
                    if client:
                        await client.session.close()

        return all(result_list)

    @helper
    @gas_checker
    async def smart_bridge(self, dapp_id: int = None):
        client = None
        fee_client = None
        while True:
            try:
                from functions import bridge_utils

                dapp_chains, dapp_tokens, limiter = {
                    1: (ACROSS_CHAIN_ID_FROM, ACROSS_TOKEN_NAME, ACROSS_AMOUNT_LIMITER),
                    2: (BUNGEE_CHAIN_ID_FROM, BUNGEE_TOKEN_NAME, BUNGEE_AMOUNT_LIMITER),
                    3: (LAYERSWAP_CHAIN_ID_FROM, LAYERSWAP_TOKEN_NAME, LAYERSWAP_AMOUNT_LIMITER),
                    4: (NITRO_CHAIN_ID_FROM, NITRO_TOKEN_NAME, NITRO_AMOUNT_LIMITER),
                    5: (ORBITER_CHAIN_ID_FROM, ORBITER_TOKEN_NAME, ORBITER_AMOUNT_LIMITER),
                    6: (OWLTO_CHAIN_ID_FROM, OWLTO_TOKEN_NAME, OWLTO_AMOUNT_LIMITER),
                    7: (RELAY_CHAIN_ID_FROM, RELAY_TOKEN_NAME, RELAY_AMOUNT_LIMITER),
                    8: (RHINO_CHAIN_ID_FROM, RHINO_TOKEN_NAME, RHINO_AMOUNT_LIMITER),
                    9: (NATIVE_CHAIN_ID_FROM, NATIVE_TOKEN_NAME, NATIVE_AMOUNT_LIMITER),
                }[dapp_id]

                if len(dapp_tokens) == 2:
                    from_token_name, to_token_name = dapp_tokens
                else:
                    from_token_name, to_token_name = dapp_tokens, dapp_tokens

                dapp_tokens = [from_token_name for _ in dapp_chains]

                client, chain_index, balance, _, balance_data = await self.balance_searcher(
                    chains=dapp_chains, tokens=dapp_tokens, omni_check=False
                )

                fee_client = await client.new_client(dapp_chains[chain_index])
                chain_from_id, token_name = dapp_chains[chain_index], from_token_name

                switch_id = BRIDGE_SWITCH_CONTROL.get(dapp_id, dapp_id)

                source_chain_name, destination_chain, amount, dst_chain_id = await client.get_bridge_data(
                    chain_from_id=chain_from_id, dapp_id=switch_id, settings_id=dapp_id
                )

                from_chain_name = client.network.name
                to_chain_name = CHAIN_NAME[dst_chain_id]
                from_token_addr = TOKENS_PER_CHAIN[from_chain_name][from_token_name]

                if to_token_name == 'USDC':
                    to_token_addr = TOKENS_PER_CHAIN[to_chain_name].get('USDC.e')
                    if not to_token_addr:
                        to_token_addr = TOKENS_PER_CHAIN[to_chain_name]['USDC']
                else:
                    to_token_addr = TOKENS_PER_CHAIN[to_chain_name][to_token_name]

                balance_in_usd, token_price = balance_data
                limit_amount, wanted_to_hold_amount = limiter
                min_wanted_amount, max_wanted_amount = min(wanted_to_hold_amount), max(wanted_to_hold_amount)
                fee_bridge_data = (source_chain_name, destination_chain, amount, dst_chain_id,
                                   from_token_name, to_token_name, from_token_addr, to_token_addr)

                if balance_in_usd >= limit_amount:
                    bridge_fee = await bridge_utils(
                        fee_client, switch_id, chain_from_id, fee_bridge_data, need_fee=True)
                    min_hold_balance = random.uniform(min_wanted_amount, max_wanted_amount) / token_price
                    if balance - bridge_fee - min_hold_balance > 0:
                        if balance < amount + bridge_fee and from_token_name == client.token:
                            bridge_amount = self.client.custom_round(amount - bridge_fee, 6)
                        else:
                            bridge_amount = amount
                        if balance - bridge_amount < min_hold_balance:
                            need_to_freeze_amount = min_hold_balance - (balance - bridge_amount)
                            bridge_amount = self.client.custom_round(bridge_amount - need_to_freeze_amount, 6)

                        if bridge_amount < 0:
                            raise CriticalException(
                                f'Set BRIDGE_AMOUNT_LIMITER[2 value] lower than {wanted_to_hold_amount}. '
                                f'Current amount = {bridge_amount} {from_token_name}')

                        bridge_amount_in_usd = bridge_amount * token_price

                        bridge_data = (source_chain_name, destination_chain, bridge_amount, dst_chain_id,
                                       from_token_name, to_token_name, from_token_addr, to_token_addr)

                        if balance_in_usd >= bridge_amount_in_usd:
                            return await bridge_utils(client, switch_id, chain_from_id, bridge_data)

                        info = f"{balance_in_usd:.2f}$ < {bridge_amount_in_usd:.2f}$"
                        raise SoftwareExceptionHandled(f'Account {token_name} balance < wanted bridge amount: {info}')

                    full_need_amount = self.client.custom_round(bridge_fee + min_hold_balance, 6)
                    info = f"{balance:.2f} {token_name} < {full_need_amount:.2f} {token_name}"
                    raise SoftwareExceptionHandled(f'Account {token_name} balance < bridge fee + hold amount: {info}')

                info = f"{balance_in_usd:.2f}$ < {limit_amount:.2f}$"
                raise SoftwareExceptionHandled(f'Account {token_name} balance < wanted limit amount: {info}')

            except CriticalException as error:
                raise error
            except Exception as error:
                raise error
            finally:
                if client:
                    await client.session.close()
                if fee_client:
                    await fee_client.session.close()

