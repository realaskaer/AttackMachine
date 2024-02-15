import random
import traceback

from modules import Logger, RequestClient
from general_settings import AMOUNT_PERCENT_WRAPS
from modules.interfaces import SoftwareException, SoftwareExceptionWithoutRetry
from utils.tools import helper, gas_checker, sleep
from config import (
    ETH_PRICE, TOKENS_PER_CHAIN, LAYERZERO_WRAPED_NETWORKS, LAYERZERO_NETWORKS_DATA,
    TOKENS_PER_CHAIN2, CHAIN_NAME, OKX_NETWORKS_NAME, BINGX_NETWORKS_NAME, BINANCE_NETWORKS_NAME, CEX_WRAPPED_ID,
    COINGECKO_TOKEN_API_NAMES
)
from settings import (
    CEX_BALANCE_WANTED, STARGATE_CHAINS, STARGATE_TOKENS, L2PASS_ATTACK_NFT, ZERIUS_ATTACK_NFT,
    SHUFFLE_ATTACK, COREDAO_CHAINS, COREDAO_TOKENS, OKX_WITHDRAW_DATA, BINANCE_DEPOSIT_DATA,
    BINGX_WITHDRAW_DATA, SHUFFLE_NFT_ATTACK, BINANCE_WITHDRAW_DATA, ALL_DST_CHAINS,
    CEX_DEPOSIT_LIMITER, RHINO_CHAIN_ID_FROM, LAYERSWAP_CHAIN_ID_FROM, ORBITER_CHAIN_ID_FROM,
    ACROSS_CHAIN_ID_FROM, BRIDGE_AMOUNT_LIMITER, WHALE_ATTACK_NFT, RELAY_CHAIN_ID_FROM, SRC_CHAIN_MERKLY,
    SRC_CHAIN_L2PASS, SRC_CHAIN_ZERIUS, DST_CHAIN_MERKLY_REFUEL, DST_CHAIN_L2PASS_REFUEL, DST_CHAIN_ZERIUS_REFUEL,
    SRC_CHAIN_WHALE, DST_CHAIN_WHALE_REFUEL, DST_CHAIN_MERKLY_NFT, DST_CHAIN_L2PASS_NFT, DST_CHAIN_ZERIUS_NFT,
    DST_CHAIN_WHALE_NFT, MERKLY_ATTACK_NFT, L2PASS_ATTACK_REFUEL, MERKLY_ATTACK_REFUEL, WHALE_ATTACK_REFUEL,
    ZERIUS_ATTACK_REFUEL, L0_SEARCH_DATA, OWLTO_CHAIN_ID_FROM, ACROSS_TOKEN_NAME, ORBITER_TOKEN_NAME, OWLTO_TOKEN_NAME,
    LAYERSWAP_TOKEN_NAME, RELAY_TOKEN_NAME, RHINO_TOKEN_NAME, OKX_DEPOSIT_DATA, BINGX_DEPOSIT_DATA,
    SRC_CHAIN_MERKLY_WORMHOLE, SRC_CHAIN_MERKLY_POLYHEDRA, SRC_CHAIN_MERKLY_HYPERLANE, DST_CHAIN_MERKLY_WORMHOLE,
    DST_CHAIN_MERKLY_POLYHEDRA, DST_CHAIN_MERKLY_HYPERLANE, WORMHOLE_TOKENS_AMOUNT, HYPERLANE_TOKENS_AMOUNT,
    DST_CHAIN_MERKLY_POLYHEDRA_REFUEL, CEX_VOLUME_MODE, BRIDGE_VOLUME_MODE
)


class Custom(Logger, RequestClient):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)
        RequestClient.__init__(self, client)

    async def collect_eth_util(self):
        from functions import swap_odos, swap_oneinch, swap_openocean, swap_xyfinance, swap_rango

        self.logger_msg(*self.client.acc_info, msg=f"Started collecting tokens in ETH")

        func = {
            'Base': [swap_rango, swap_odos, swap_oneinch, swap_openocean, swap_xyfinance],
            'Linea': [swap_rango, swap_openocean, swap_xyfinance],
            'Scroll': [swap_rango, swap_openocean, swap_xyfinance],
            'zkSync': [swap_rango, swap_openocean, swap_xyfinance, swap_odos, swap_oneinch]
        }[self.client.network.name]

        wallet_balance = {k: await self.client.get_token_balance(k, False)
                          for k, v in TOKENS_PER_CHAIN[self.client.network.name].items()}
        valid_wallet_balance = {k: v[1] for k, v in wallet_balance.items() if v[0] != 0}
        eth_price = ETH_PRICE

        for token in ['ETH', 'WETH']:
            if token in valid_wallet_balance:
                valid_wallet_balance[token] *= eth_price

        if valid_wallet_balance['ETH'] < 0.5:
            self.logger_msg(*self.client.acc_info, msg=f'Account has not enough ETH for swap', type_msg='warning')
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
                                module_func = random.choice(func)
                                try:
                                    self.logger_msg(*self.client.acc_info, msg=f'Launching swap module', type_msg='warning')
                                    result = await module_func(self.client.account_name, self.client.private_key,
                                                               self.client.network, self.client.proxy_init, swapdata=data)
                                    if not result:
                                        counter += 1
                                except:
                                    counter += 1
                                    pass
                                if result or counter == 3:
                                    break
                        else:
                            self.logger_msg(*self.client.acc_info, msg=f"{token_name} balance < 1$")
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
        from functions import okx_withdraw_util

        self.logger_msg(*self.client.acc_info, msg=f"Stark check all balance to make average")

        amount = CEX_BALANCE_WANTED
        wanted_amount_in_usd = float(f'{amount * ETH_PRICE:.2f}')

        wallet_balance = {k: await self.client.get_token_balance(k, False)
                          for k, v in TOKENS_PER_CHAIN[self.client.network.name].items()}
        valid_wallet_balance = {k: v[1] for k, v in wallet_balance.items() if v[0] != 0}
        eth_price = ETH_PRICE

        if 'ETH' in valid_wallet_balance:
            valid_wallet_balance['ETH'] = valid_wallet_balance['ETH'] * eth_price

        valid_wallet_balance = {k: round(v, 7) for k, v in valid_wallet_balance.items()}

        sum_balance_in_usd = sum(valid_wallet_balance.values())

        if wanted_amount_in_usd > sum_balance_in_usd:
            need_to_withdraw = float(f"{(wanted_amount_in_usd - sum_balance_in_usd) / eth_price:.6f}")

            self.logger_msg(*self.client.acc_info, msg=f"Not enough balance on account, start OKX withdraw module")

            return await okx_withdraw_util(self.client, want_balance=need_to_withdraw)
        raise SoftwareExceptionWithoutRetry('Account has enough tokens on balance!')

    @helper
    async def wraps_abuser(self):
        from functions import swap_odos, swap_oneinch, swap_xyfinance, swap_rango

        func = {
            'Base': [swap_rango, swap_odos, swap_oneinch, swap_xyfinance],
            'Linea': [swap_rango, swap_xyfinance],
            'Scroll': [swap_rango, swap_xyfinance],
            'zkSync': [swap_rango, swap_xyfinance, swap_odos, swap_oneinch]
        }[self.client.network.name]

        current_tokens = list(TOKENS_PER_CHAIN[self.client.network.name].items())[:2]

        wallet_balance = {k: await self.client.get_token_balance(k, False) for k, v in current_tokens}
        valid_wallet_balance = {k: v[1] for k, v in wallet_balance.items() if v[0] != 0}
        eth_price = ETH_PRICE

        if 'ETH' in valid_wallet_balance:
            valid_wallet_balance['ETH'] = valid_wallet_balance['ETH'] * eth_price

        if 'WETH' in valid_wallet_balance:
            valid_wallet_balance['WETH'] = valid_wallet_balance['WETH'] * eth_price

        max_token = max(valid_wallet_balance, key=lambda x: valid_wallet_balance[x])
        percent = round(random.uniform(*AMOUNT_PERCENT_WRAPS), 9) / 100 if max_token == 'ETH' else 1
        amount_in_wei = int(wallet_balance[max_token][0] * percent)
        amount = float(f"{amount_in_wei / 10 ** 18:.6f}")

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

                except:
                    pass
                if result or counter == 3:
                    break

        else:
            self.logger_msg(*self.client.acc_info, msg=f"{from_token_name} balance is too low (lower 1$)")

        return True

    @helper
    @gas_checker
    async def smart_bridge_l0(self, dapp_id:int = None):
        clients = []
        try:
            from functions import Stargate, CoreDAO

            dapp_config = {
                1: (Stargate, STARGATE_TOKENS, STARGATE_CHAINS),
                2: (CoreDAO, COREDAO_TOKENS, COREDAO_CHAINS)
            }[dapp_id]

            class_name, tokens, chains = dapp_config

            clients = [await self.client.new_client(LAYERZERO_WRAPED_NETWORKS[chain])
                       for chain in chains]
            balances = [await client.get_token_balance(omnicheck=True, token_name=token, check_symbol=True)
                        for client, token in zip(clients, tokens)]

            if all(balance_in_wei == 0 for balance_in_wei, _, _ in balances):
                raise SoftwareException('Insufficient balances in all networks!')

            index = balances.index(max(balances, key=lambda x: x[1] * (ETH_PRICE if x[2] == 'ETH' else 1)))
            current_client = clients[index]
            from_token_name = tokens[index]
            balance_in_wei, balance, _ = balances[index]

            if (balance * ETH_PRICE < 1 and from_token_name == 'ETH') or (balance < 1 and from_token_name != 'ETH'):
                raise SoftwareException('Balance on source chain < 1$!')

            amount_in_wei = balance_in_wei if from_token_name != 'ETH' else int(
                (await current_client.get_smart_amount(need_percent=True)) * 10 ** 18)

            dst_chain = random.choice([chain for i, chain in enumerate(chains) if i != index])
            src_chain_name = current_client.network.name
            dst_chain_name, dst_chain_id, _, _ = LAYERZERO_NETWORKS_DATA[dst_chain]
            to_token_name = tokens[chains.index(dst_chain)]

            if from_token_name != 'ETH':
                contract = current_client.get_contract(TOKENS_PER_CHAIN2[current_client.network.name][from_token_name])
                decimals = await contract.functions.decimals().call()
            else:
                decimals = 18

            amount = f"{amount_in_wei / 10 ** decimals:.4f}"

            swapdata = (src_chain_name, dst_chain_name, dst_chain_id,
                        from_token_name, to_token_name, amount, amount_in_wei)

            return await class_name(current_client).bridge(swapdata=swapdata)
        finally:
            for client in clients:
                await client.session.close()

    @helper
    async def swap_bridged_usdc(self):
        from functions import swap_woofi

        amount_in_wei, amount, _ = await self.client.get_token_balance('USDC')
        data = 'USDC', 'USDC.e', amount, amount_in_wei

        if amount_in_wei == 0:
            raise SoftwareException("Insufficient USDC balances")

        return await swap_woofi(self.client.account_name, self.client.private_key,
                                self.client.network, self.client.proxy_init, swapdata=data)

    @helper
    @gas_checker
    async def layerzero_attack(self, dapp_id:int = None, dapp_mode:int = None):
        from functions import omnichain_util

        class_id, attack_data = {
            1: (1, (L2PASS_ATTACK_REFUEL, L2PASS_ATTACK_NFT)),
            2: (2, (MERKLY_ATTACK_REFUEL, MERKLY_ATTACK_NFT)),
            3: (3, (WHALE_ATTACK_REFUEL, WHALE_ATTACK_NFT)),
            4: (4, (ZERIUS_ATTACK_REFUEL, ZERIUS_ATTACK_NFT)),
        }[dapp_id]

        attack_data_without_none = []

        if dapp_mode == 1:
            attack_data = attack_data[0]
            if SHUFFLE_ATTACK:
                random.shuffle(attack_data_without_none)
        elif dapp_mode == 2:
            attack_data = attack_data[1]
            if SHUFFLE_NFT_ATTACK:
                random.shuffle(attack_data_without_none)

        for path in attack_data:
            if isinstance(path, tuple):
                module = random.choice(path)
                if module:
                    attack_data_without_none.append(module)
                continue
            attack_data_without_none.append(path)

        for chain_id_from, attack_info in attack_data_without_none:
            if isinstance(attack_info, (list, tuple)):
                attack_info = random.choice(attack_info)

            chain_id_from = LAYERZERO_WRAPED_NETWORKS[chain_id_from]

            if dapp_mode == 1:
                chain_to_id, amount = attack_info
                attack_data = {
                    attack_info: (amount, round(amount * 1.1, 7))
                }
            elif dapp_mode == 2:
                attack_data = attack_info

            await omnichain_util(
                self.client.account_name, self.client.private_key, self.client.proxy_init,
                chain_id_from, attack_data=attack_data, dapp_id=class_id, dapp_mode=dapp_mode
            )

            await sleep(self)

        return True

    @helper
    async def smart_cex_deposit_l0(self, dapp_id:int = None):
        from functions import cex_deposit_util
        from config import OKX_DEPOSIT_L0_DATA

        search_chains, search_tokens = {
            1: (STARGATE_CHAINS, STARGATE_TOKENS),
            2: (COREDAO_CHAINS, COREDAO_TOKENS)
        }[L0_SEARCH_DATA]

        deposit_amount = {
            1: OKX_DEPOSIT_DATA,
            2: BINGX_DEPOSIT_DATA,
            3: BINANCE_DEPOSIT_DATA,
        }[dapp_id]

        client, index, _, _ = await self.balance_searcher(search_chains, search_tokens)

        dep_chain = search_chains[index]
        dep_token = search_tokens[index]
        amount = await client.get_smart_amount(deposit_amount, token_name=dep_token)
        deposit_data = OKX_DEPOSIT_L0_DATA[dep_chain][dep_token], (amount, amount)

        result = await cex_deposit_util(self.client, dapp_id=dapp_id, deposit_data=deposit_data)

        await client.session.close()

        return result

    async def balance_searcher(self, chains, tokens, omni_check:bool = True, bridge_check:bool = False):

        clients = [await self.client.new_client(LAYERZERO_WRAPED_NETWORKS[chain] if omni_check else chain)
                   for chain in chains]

        balances = [await client.get_token_balance(omnicheck=omni_check, token_name=token, bridge_check=bridge_check)
                    for client, token in zip(clients, tokens)]

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

        self.logger_msg(
            *self.client.acc_info,
            msg=f"Detected {round(balances[index][1], 5)} {tokens[index]} in {clients[index].network.name}",
            type_msg='success')

        return clients[index], index, balances[index][1], balances_in_usd[index]

    @helper
    @gas_checker
    async def smart_random_approve(self):
        client = None
        try:
            from config import (IZUMI_CONTRACTS, MAVERICK_CONTRACTS, RANGO_CONTRACTS, ODOS_CONTRACTS, ONEINCH_CONTRACTS,
                                OPENOCEAN_CONTRACTS, PANCAKE_CONTRACTS, SUSHISWAP_CONTRACTS,
                                UNISWAP_CONTRACTS, STARGATE_CONTRACTS, WOOFI_CONTRACTS, XYFINANCE_CONTRACTS, TOKENS_PER_CHAIN)

            all_contracts = {
                "Rango.Exchange": RANGO_CONTRACTS,
                "Maverick": MAVERICK_CONTRACTS,
                "SushiSwap": SUSHISWAP_CONTRACTS,
                "Uniswap": UNISWAP_CONTRACTS,
                "Stargate": STARGATE_CONTRACTS,
                "PancakeSwap": PANCAKE_CONTRACTS,
                "WooFi": WOOFI_CONTRACTS,
                "iZumi": IZUMI_CONTRACTS,
                "ODOS": ODOS_CONTRACTS,
                "1inch": ONEINCH_CONTRACTS,
                "OpenOcean": OPENOCEAN_CONTRACTS,
                "XYfinance": XYFINANCE_CONTRACTS,
            }

            client, index, _, _ = await self.balance_searcher(STARGATE_CHAINS, STARGATE_TOKENS)

            network_name = client.network.name

            all_network_contracts = {
                name: contracts[network_name]['router']
                for name, contracts in all_contracts.items()
                if contracts.get(network_name)
            }

            approve_contracts = [(k, v) for k, v in all_network_contracts.items()]
            contract_name, approve_contract = random.choice(approve_contracts)
            native = [client.network.token, f"W{client.network.token}"]
            token_contract = random.choice([i for i in list(TOKENS_PER_CHAIN[network_name].items()) if i[0] not in native])
            amount = random.uniform(1, 10000)
            amount_in_wei = self.client.to_wei(amount, await client.get_decimals(token_contract[0]))

            message = f"Approve {amount:.4f} {token_contract[0]} for {contract_name}"
            self.logger_msg(*client.acc_info, msg=message)

            return await client.check_for_approved(token_contract[1], approve_contract, amount_in_wei,
                                                   without_bal_check=True)
        finally:
            await client.session.close()

    @helper
    @gas_checker
    async def smart_layerzero_util(self, dapp_id: int = None, dapp_mode: int = None):
        from functions import omnichain_util

        class_id, src_chains, dst_tuple_data = {
            1: (1, SRC_CHAIN_L2PASS, (DST_CHAIN_L2PASS_REFUEL, DST_CHAIN_L2PASS_NFT)),
            2: (2, SRC_CHAIN_MERKLY, (DST_CHAIN_MERKLY_REFUEL, DST_CHAIN_MERKLY_NFT)),
            3: (3, SRC_CHAIN_WHALE, (DST_CHAIN_WHALE_REFUEL, DST_CHAIN_WHALE_NFT)),
            4: (4, SRC_CHAIN_ZERIUS, (DST_CHAIN_ZERIUS_REFUEL, DST_CHAIN_ZERIUS_NFT)),
        }[dapp_id]

        dst_datas, module_name = {
            1: (list(dst_tuple_data[0].items()), 'refuel'),
            2: (dst_tuple_data[1], 'bridge')
        }[dapp_mode]

        random.shuffle(src_chains)
        random.shuffle(dst_datas)

        result = False
        action_flag = False
        for dst_data in dst_datas:
            chain_id_to = LAYERZERO_WRAPED_NETWORKS[dst_data[0]]
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
                        chain_id_from = LAYERZERO_WRAPED_NETWORKS[src_chain]
                        self.logger_msg(
                            *self.client.acc_info,
                            msg=f"Detected funds to {module_name} {CHAIN_NAME[chain_id_to]} from {CHAIN_NAME[chain_id_from]}",
                            type_msg='success')

                        result = await omnichain_util(
                            self.client.account_name, self.client.private_key, self.client.proxy_init,
                            chain_from_id=src_chain, dapp_id=class_id, dapp_mode=dapp_mode, attack_data=attack_data
                        )

                        if not ALL_DST_CHAINS:
                            return True

                        if ALL_DST_CHAINS:
                            random.shuffle(src_chains)

                            if result:
                                break

                except Exception as error:
                    traceback.print_exc()
                    self.logger_msg(
                        *self.client.acc_info,
                        msg=f"Exception during smart {module_name}: {error}", type_msg='warning'
                    )

            if not result and ALL_DST_CHAINS:
                self.logger_msg(
                    *self.client.acc_info,
                    msg=f"Can`t {module_name} to {CHAIN_NAME[chain_id_to]} from those SRC networks\n",
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
    async def merkly_omnichain_util(self, dapp_mode:int, dapp_function:int):
        from functions import omnichain_util

        module_name, src_chains, dst_chains, token_amounts, refuel_data = {
            1: ('Wormhole', SRC_CHAIN_MERKLY_WORMHOLE, DST_CHAIN_MERKLY_WORMHOLE, WORMHOLE_TOKENS_AMOUNT, 0),
            2: ('Polyhedra', SRC_CHAIN_MERKLY_POLYHEDRA, DST_CHAIN_MERKLY_POLYHEDRA, 0, DST_CHAIN_MERKLY_POLYHEDRA_REFUEL),
            3: ('Hyperlane', SRC_CHAIN_MERKLY_HYPERLANE, DST_CHAIN_MERKLY_HYPERLANE, HYPERLANE_TOKENS_AMOUNT, 0),
        }[dapp_mode]

        dst_datas, module_func_name = {
            1: (list(refuel_data.items()) if dapp_function == 1 else 0, 'refuel'),
            2: (dst_chains, 'NFT bridge'),
            3: (dst_chains, 'token bridge')
        }[dapp_function]

        random.shuffle(src_chains)
        random.shuffle(dst_datas)
        func_mode = f"{module_func_name} {module_name}"

        result = False
        action_flag = False

        for dst_data in dst_datas:
            chain_id_to = LAYERZERO_WRAPED_NETWORKS[dst_data]
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
                        chain_from_id=src_chain, dapp_id=2, dapp_mode=func_mode, attack_data=attack_data,
                        need_check=True
                    )

                    if action_flag:
                        chain_id_from = LAYERZERO_WRAPED_NETWORKS[src_chain]
                        self.logger_msg(
                            *self.client.acc_info,
                            msg=f"Detected funds to {module_func_name} {CHAIN_NAME[chain_id_to]} from {CHAIN_NAME[chain_id_from]}",
                            type_msg='success')

                        result = await omnichain_util(
                            self.client.account_name, self.client.private_key, self.client.proxy_init,
                            chain_from_id=src_chain, dapp_id=2, dapp_mode=func_mode, attack_data=attack_data
                        )

                        if not ALL_DST_CHAINS:
                            return True

                        if ALL_DST_CHAINS:
                            random.shuffle(src_chains)

                            if result:
                                break

                except Exception as error:
                    self.logger_msg(
                        *self.client.acc_info,
                        msg=f"Exception during smart {module_func_name}: {error}", type_msg='warning'
                    )

            if not result and ALL_DST_CHAINS:
                self.logger_msg(
                    *self.client.acc_info,
                    msg=f"Can`t {module_func_name} to {CHAIN_NAME[chain_id_to]} from those SRC networks\n",
                    type_msg='warning'
                )

        if action_flag is False:
            self.logger_msg(
                *self.client.acc_info, msg=f"Can`t detect funds in all networks!", type_msg='warning')

        if ALL_DST_CHAINS:
            return True
        return result

    @helper
    async def smart_cex_withdraw(self, dapp_id:int):
        from functions import okx_withdraw_util, bingx_withdraw_util, binance_withdraw_util

        func, multi_withdraw_data = {
            1: (okx_withdraw_util, OKX_WITHDRAW_DATA),
            2: (bingx_withdraw_util, BINGX_WITHDRAW_DATA),
            3: (binance_withdraw_util, BINANCE_WITHDRAW_DATA)
        }[dapp_id]

        random.shuffle(multi_withdraw_data)
        result_list = []

        for data in multi_withdraw_data:
            current_data = data
            if isinstance(data[0], list):
                current_data = random.choice(data)
                if not current_data:
                    continue

            network, amount = current_data
            if isinstance(amount[0], str):
                raise SoftwareExceptionWithoutRetry('CEX withdrawal does not support % of the amount')

            try:
                result_list.append(await func(self.client, withdraw_data=(network, amount)))

            except Exception as error:
                self.logger_msg(
                    *self.client.acc_info, msg=f"Withdraw from CEX failed. Error: {error}", type_msg='error')

            await sleep(self)

        return all(result_list)

    @helper
    @gas_checker
    async def smart_cex_deposit(self, dapp_id:int):
        client = None
        try:
            from functions import cex_deposit_util

            class_id, multi_deposit_data, cex_config = {
                1: (1, OKX_DEPOSIT_DATA, OKX_NETWORKS_NAME),
                2: (2, BINGX_DEPOSIT_DATA, BINGX_NETWORKS_NAME),
                3: (3, BINANCE_DEPOSIT_DATA, BINANCE_NETWORKS_NAME),
            }[dapp_id]

            result_list = []
            for data in multi_deposit_data:

                current_data = data
                if isinstance(data[0], list):
                    current_data = random.choice(data)
                    if not current_data:
                        continue

                networks, amount = current_data
                if isinstance(networks, tuple):
                    dapp_tokens = [f"{cex_config[network].split('-')[0]}{'.e' if network in [29, 30] else ''}"
                                   for network in networks]
                    dapp_chains = [CEX_WRAPPED_ID[chain] for chain in networks]
                else:
                    dapp_tokens = [f"{cex_config[networks].split('-')[0]}{'.e' if networks in [29, 30] else ''}"]
                    dapp_chains = [CEX_WRAPPED_ID[networks]]

                client, chain_index, balance, balance_data = await self.balance_searcher(
                    chains=dapp_chains, tokens=dapp_tokens, omni_check=False,
                )

                balance_in_usd, token_price = balance_data
                dep_token = dapp_tokens[chain_index]
                dep_network = networks if isinstance(networks, int) else networks[chain_index]
                limit_amount, wanted_to_hold_amount = CEX_DEPOSIT_LIMITER
                min_wanted_amount, max_wanted_amount = min(wanted_to_hold_amount), max(wanted_to_hold_amount)

                if balance_in_usd > limit_amount:

                    if CEX_VOLUME_MODE:
                        dep_amount = round(balance_in_usd - (random.uniform(min_wanted_amount, max_wanted_amount)), 6)
                    else:
                        dep_amount = await client.get_smart_amount(amount)
                    dep_amount_in_usd = dep_amount * token_price

                    if balance_in_usd > dep_amount_in_usd:

                        if (min_wanted_amount <= (balance_in_usd - dep_amount_in_usd) <= max_wanted_amount
                                or CEX_VOLUME_MODE):

                            deposit_data = dep_network, (dep_amount, dep_amount)

                            if len(multi_deposit_data) == 1:
                                return await cex_deposit_util(client, dapp_id=class_id, deposit_data=deposit_data)
                            else:
                                result_list.append(
                                    await cex_deposit_util(client, dapp_id=class_id, deposit_data=deposit_data)
                                )
                                await client.session.close()
                                continue

                        hold_amount_in_usd = balance_in_usd - dep_amount_in_usd
                        info = f"{min_wanted_amount:.2f}$ <= {hold_amount_in_usd:.2f}$ <= {max_wanted_amount:.2f}$"
                        raise SoftwareExceptionWithoutRetry(f'Account balance will be not in wanted hold amount: {info}')

                    info = f"{balance_in_usd:.2f}$ < {dep_amount_in_usd:.2f}$"
                    raise SoftwareExceptionWithoutRetry(f'Account {dep_token} balance < wanted deposit amount: {info}')

                info = f"{balance_in_usd:.2f}$ < {limit_amount:.2f}$"
                raise SoftwareExceptionWithoutRetry(f'Account {dep_token} balance < wanted limit amount: {info}')
            return all(result_list)
        finally:
            await client.session.close()

    @helper
    @gas_checker
    async def smart_bridge(self, dapp_id:int = None):
        client = None
        try:
            from functions import bridge_utils

            bridge_app_id, dapp_chains, dapp_token = {
                1: (1, ACROSS_CHAIN_ID_FROM, ACROSS_TOKEN_NAME),
                2: (2, LAYERSWAP_CHAIN_ID_FROM, LAYERSWAP_TOKEN_NAME),
                3: (3, ORBITER_CHAIN_ID_FROM, ORBITER_TOKEN_NAME),
                4: (4, OWLTO_CHAIN_ID_FROM, OWLTO_TOKEN_NAME),
                5: (5, RELAY_CHAIN_ID_FROM, RELAY_TOKEN_NAME),
                6: (6, RHINO_CHAIN_ID_FROM, RHINO_TOKEN_NAME),
            }[dapp_id]

            dapp_tokens = [dapp_token for _ in dapp_chains]

            client, chain_index, balance, balance_data = await self.balance_searcher(
                chains=dapp_chains, tokens=dapp_tokens, omni_check=False, bridge_check=True
            )

            chain_from_id, token_name = dapp_chains[chain_index], dapp_token

            source_chain_name, destination_chain, amount, dst_chain_id = await client.get_bridge_data(
                chain_from_id=chain_from_id, dapp_id=bridge_app_id
            )

            from_token_addr = None
            to_token_addr = None
            from_chain_name = client.network.name
            to_chain_name = CHAIN_NAME[dst_chain_id]
            if token_name == 'USDC':
                from_token_addr = TOKENS_PER_CHAIN[from_chain_name].get('USDC.e')
                to_token_addr = TOKENS_PER_CHAIN[to_chain_name].get('USDC.e')
            from_token_addr = from_token_addr if from_token_addr else TOKENS_PER_CHAIN[from_chain_name][token_name]
            to_token_addr = to_token_addr if to_token_addr else TOKENS_PER_CHAIN[to_chain_name][token_name]

            balance_in_usd, token_price = balance_data
            limit_amount, wanted_to_hold_amount = BRIDGE_AMOUNT_LIMITER
            min_wanted_amount, max_wanted_amount = min(wanted_to_hold_amount), max(wanted_to_hold_amount)
            bridge_data = (source_chain_name, destination_chain, amount,
                           dst_chain_id, token_name, from_token_addr, to_token_addr)

            if balance_in_usd > limit_amount:

                if BRIDGE_VOLUME_MODE:
                    bridge_amount = round(balance_in_usd - (random.uniform(min_wanted_amount, max_wanted_amount)), 6)
                else:
                    bridge_amount = await bridge_utils(client, bridge_app_id, chain_from_id, bridge_data, need_fee=True)
                bridge_amount_in_usd = bridge_amount * token_price

                if balance_in_usd > bridge_amount_in_usd:

                    if (min_wanted_amount <= (balance_in_usd - bridge_amount_in_usd) <= max_wanted_amount
                            or BRIDGE_VOLUME_MODE):

                        return await bridge_utils(client, bridge_app_id, chain_from_id, bridge_data)

                    hold_amount_in_usd = balance_in_usd - bridge_amount_in_usd
                    info = f"{min_wanted_amount:.2f}$ <= {hold_amount_in_usd:.2f}$ <= {max_wanted_amount:.2f}$"
                    raise SoftwareExceptionWithoutRetry(f'Account balance will be not in wanted hold amount: {info}')

                info = f"{balance_in_usd:.2f}$ < {bridge_amount_in_usd:.2f}$"
                raise SoftwareExceptionWithoutRetry(f'Account {token_name} balance < wanted bridge amount: {info}')

            info = f"{balance_in_usd:.2f}$ < {limit_amount:.2f}$"
            raise SoftwareExceptionWithoutRetry(f'Account {token_name} balance < wanted limit amount: {info}')
        finally:
            await client.session.close()
