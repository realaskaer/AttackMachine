import random

from config import ETH_PRICE, TOKENS_PER_CHAIN, LAYERZERO_WRAPED_NETWORKS, LAYERZERO_NETWORKS_DATA, \
    TOKENS_PER_CHAIN2, CHAIN_NAME
from modules import Logger, RequestClient
from general_settings import GLOBAL_NETWORK, AMOUNT_PERCENT_WRAPS
from modules.interfaces import SoftwareException
from settings import OKX_BALANCE_WANTED, STARGATE_CHAINS, STARGATE_TOKENS, \
    L2PASS_ATTACK_NFT, \
    ZERIUS_ATTACK_NFT, SHUFFLE_ATTACK, COREDAO_CHAINS, COREDAO_TOKENS, OKX_MULTI_WITHDRAW, OKX_DEPOSIT_AMOUNT, \
    BINGX_MULTI_WITHDRAW, SHUFFLE_NFT_ATTACK, BINANCE_MULTI_WITHDRAW, SMART_REFUEL_BATCH
from utils.tools import helper, gas_checker, sleep


class Custom(Logger, RequestClient):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)
        RequestClient.__init__(self, client)

    async def collect_eth_util(self):
        from functions import swap_odos, swap_oneinch, swap_openocean, swap_xyfinance, swap_rango, swap_avnu
        if GLOBAL_NETWORK == 9:
            await self.client.initialize_account()

        self.logger_msg(*self.client.acc_info, msg=f"Start collecting tokens in ETH")

        func = {
            'Base': [swap_rango, swap_odos, swap_oneinch, swap_openocean, swap_xyfinance],
            'Linea': [swap_rango, swap_openocean, swap_xyfinance],
            'Scroll': [swap_openocean, swap_xyfinance],
            'Starknet': [swap_rango, swap_avnu],
            'zkSync Era': [swap_rango, swap_openocean, swap_xyfinance, swap_odos, swap_oneinch]
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
    @gas_checker
    async def collect_eth(self):
        await self.collect_eth_util()

        return True

    @helper
    @gas_checker
    async def balance_average(self):
        from functions import okx_withdraw

        self.logger_msg(*self.client.acc_info, msg=f"Stark check all balance to make average")

        amount = OKX_BALANCE_WANTED
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

            return await okx_withdraw(self.client.account_name, self.client.private_key, self.client.network,
                                      self.client.proxy_init, want_balance=need_to_withdraw)
        raise SoftwareException('Account has enough tokens on balance!')

    @helper
    @gas_checker
    async def wraps_abuser(self):
        await self.wraps_abuser_util()

        return True

    @helper
    @gas_checker
    async def smart_wraps_abuser(self):
        from functions import wrap_abuser

        await self.wraps_abuser_util()

        return True

    async def wraps_abuser_util(self):
        from functions import swap_odos, swap_oneinch, swap_xyfinance, swap_avnu

        if GLOBAL_NETWORK == 9:
            await self.client.initialize_account()

        func = {
            'Arbitrum': [swap_odos, swap_oneinch, swap_xyfinance],
            'Optimism': [swap_odos, swap_oneinch, swap_xyfinance],
            'Base': [swap_odos, swap_oneinch, swap_xyfinance],
            'Linea': [swap_xyfinance],
            'Scroll': [swap_xyfinance],
            'Starknet': [swap_avnu],
            'zkSync Era': [swap_xyfinance, swap_odos, swap_oneinch]
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
        from functions import swap_stargate, swap_coredao

        dapp_config = {
            1: (swap_stargate, STARGATE_TOKENS, STARGATE_CHAINS),
            2: (swap_coredao, COREDAO_TOKENS, COREDAO_CHAINS)
        }[dapp_id]

        func, tokens, chains = dapp_config

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

        swapdata = (src_chain_name, dst_chain_name, dst_chain_id, from_token_name, to_token_name, amount, amount_in_wei)

        try:
            return await func(current_client, swapdata=swapdata)
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
    async def refuel_attack(self, dapp_id:int = None):
        from functions import merkly_for_refuel_attack, l2pass_for_refuel_attack, zerius_for_refuel_attack
        from settings import MERKLY_ATTACK_REFUEL, ZERIUS_ATTACK_REFUEL, L2PASS_ATTACK_REFUEL

        dapp_config = {
            1: (merkly_for_refuel_attack, MERKLY_ATTACK_REFUEL),
            2: (l2pass_for_refuel_attack, L2PASS_ATTACK_REFUEL),
            3: (zerius_for_refuel_attack, ZERIUS_ATTACK_REFUEL)
        }[dapp_id]

        attack_refuel_without_none = []

        func, attack_data = dapp_config

        for path in attack_data:
            if isinstance(path, tuple):
                module = random.choice(path)
                if module:
                    attack_refuel_without_none.append(module)
                continue
            attack_refuel_without_none.append(path)

        if SHUFFLE_ATTACK:
            random.shuffle(attack_refuel_without_none)

        for chain_id_from, chain_id_to, amount in attack_refuel_without_none:
            if isinstance(chain_id_to, list):
                chain_id_to = random.choice(chain_id_to)

            refuel_data = {
                chain_id_to: (amount, round(amount * 1.1, 7))
            }

            chain_id_from = LAYERZERO_WRAPED_NETWORKS[chain_id_from]

            await func(self.client.account_name, self.client.private_key, self.client.network,
                       self.client.proxy_init, chain_id_from, attack_mode=True, attack_data=refuel_data)

            await sleep(self)

        return True

    @helper
    async def nft_attack(self, dapp_id:int = None):
        from functions import l2pass_for_nft_attack, zerius_for_nft_attack

        dapp_config = {
            1: (l2pass_for_nft_attack, L2PASS_ATTACK_NFT),
            2: (zerius_for_nft_attack, ZERIUS_ATTACK_NFT)
        }[dapp_id]

        func, attack_data = dapp_config

        attack_bridge_without_none = []

        for path in attack_data:
            if isinstance(path, tuple):
                module = random.choice(path)
                if module:
                    attack_bridge_without_none.append(module)
                continue
            attack_bridge_without_none.append(path)

        if SHUFFLE_NFT_ATTACK:
            random.shuffle(attack_bridge_without_none)

        for chain_id_from, chain_id_to in attack_bridge_without_none:
            if isinstance(chain_id_to, list):
                chain_id_to = random.choice(chain_id_to)

            chain_id_from = LAYERZERO_WRAPED_NETWORKS[chain_id_from]

            await func(self.client.account_name, self.client.private_key, self.client.network,
                       self.client.proxy_init, chain_id_from, attack_mode=True, attack_data=chain_id_to)

            await sleep(self)

        return True

    @helper
    async def cex_multi_withdraw(self, dapp_id:int, random_network:bool = False):
        from functions import okx_withdraw, bingx_withdraw, binance_withdraw

        dapp_config = {
            1: (okx_withdraw, OKX_MULTI_WITHDRAW),
            2: (bingx_withdraw, BINGX_MULTI_WITHDRAW),
            3: (binance_withdraw, BINANCE_MULTI_WITHDRAW)
        }[dapp_id]

        func, withdraw_datas = dapp_config

        if random_network:
            shuffle_withdraw = list(withdraw_datas.items())
            shuffle_withdraw = [random.choice(shuffle_withdraw)]
        else:
            shuffle_withdraw = list(withdraw_datas.items())
            random.shuffle(shuffle_withdraw)

        multi_withdraw_data = {}

        for network, amount in shuffle_withdraw:

            multi_withdraw_data['network'] = network
            multi_withdraw_data['amount'] = amount

            try:
                await func(self.client.account_name, self.client.private_key, self.client.network,
                           self.client.proxy_init, multi_withdraw_data=multi_withdraw_data)

            except Exception as error:
                self.logger_msg(
                    *self.client.acc_info, msg=f"Withdraw from CEX failed. Error: {error}", type_msg='error')

            await sleep(self)

        return True

    @helper
    async def smart_refuel(self, dapp_id:int = None):
        from functions import merkly_for_refuel_attack, l2pass_for_refuel_attack, zerius_for_refuel_attack
        from settings import (SRC_CHAIN_MERKLY, SRC_CHAIN_L2PASS, SRC_CHAIN_ZERIUS,
                              DST_CHAIN_MERKLY_REFUEL, DST_CHAIN_L2PASS_REFUEL, DST_CHAIN_ZERIUS_REFUEL)

        dapp_config = {
            1: (merkly_for_refuel_attack, SRC_CHAIN_MERKLY, DST_CHAIN_MERKLY_REFUEL),
            2: (l2pass_for_refuel_attack, SRC_CHAIN_L2PASS, DST_CHAIN_L2PASS_REFUEL),
            3: (zerius_for_refuel_attack, SRC_CHAIN_ZERIUS, DST_CHAIN_ZERIUS_REFUEL)
        }[dapp_id]

        func, src_chains, dst_data = dapp_config

        dst_datas = list(dst_data.items())

        random.shuffle(src_chains)
        random.shuffle(dst_datas)

        result = False
        refuel_flag = False
        for dst_data in dst_datas:
            chain_id_to = LAYERZERO_WRAPED_NETWORKS[dst_data[0]]
            for src_chain in src_chains:
                try:
                    refuel_data = {
                        dst_data[0]: dst_data[1]
                    }

                    chain_id_from = LAYERZERO_WRAPED_NETWORKS[src_chain]
                    refuel_flag = await func(
                        self.client.account_name, self.client.private_key, self.client.network, self.client.proxy_init,
                        chain_id_from, attack_mode=True, attack_data=refuel_data, need_check=True)

                    if refuel_flag:
                        self.logger_msg(
                            *self.client.acc_info,
                            msg=f"Detected funds to refuel {CHAIN_NAME[chain_id_to]} from {CHAIN_NAME[chain_id_from]}",
                            type_msg='success')

                        result = await func(self.client.account_name, self.client.private_key, self.client.network,
                                            self.client.proxy_init, chain_id_from, attack_mode=True,
                                            attack_data=refuel_data)

                        if not SMART_REFUEL_BATCH:
                            return True

                        if SMART_REFUEL_BATCH:
                            random.shuffle(src_chains)

                            if result:
                                break

                except Exception as error:
                    self.logger_msg(
                        *self.client.acc_info, msg=f"Warning during smart refuel: {error}", type_msg='warning')

            if not result and SMART_REFUEL_BATCH:
                self.logger_msg(
                    *self.client.acc_info, msg=f"Can`t refuel to {CHAIN_NAME[chain_id_to]} from those SRC networks\n",
                    type_msg='warning')

        if refuel_flag is False:
            self.logger_msg(
                *self.client.acc_info, msg=f"Can`t detect funds in all networks!", type_msg='warning')

        if SMART_REFUEL_BATCH:
            return True
        return False

    @helper
    async def smart_cex_deposit(self, dapp_id:int = None):
        from functions import okx_deposit
        from config import OKX_DEPOSIT_L0_DATA

        dapp_config = {
            1: (okx_deposit, STARGATE_CHAINS, STARGATE_TOKENS),
        }[dapp_id]

        func, chains, tokens = dapp_config

        client, index = await self.balance_searcher(chains, tokens)

        self.logger_msg(*self.client.acc_info, msg=f"Detected balance in {client.network.name}", type_msg='success')

        dep_chain = chains[index]
        dep_token = tokens[index]
        amount = await client.get_smart_amount(OKX_DEPOSIT_AMOUNT, token_name=dep_token)
        deposit_data = OKX_DEPOSIT_L0_DATA[dep_chain][dep_token], (amount, amount)

        result = await okx_deposit(self.client.account_name, self.client.private_key, self.client.network,
                                   self.client.proxy_init, dep_network=deposit_data[0], deposit_data=deposit_data)

        await client.session.close()

        return result

    async def balance_searcher(self, chains, tokens):
        clients = [await self.client.new_client(LAYERZERO_WRAPED_NETWORKS[chain])
                   for chain in chains]
        balances = [await client.get_token_balance(omnicheck=True, token_name=token, check_symbol=False)
                    for client, token in zip(clients, tokens)]

        index = balances.index(max(balances, key=lambda x: x[1] * (ETH_PRICE if x[2] == 'ETH' else 1)))

        for index_client, client in enumerate(clients):
            if index_client != index:
                await client.session.close()

        return clients[index], index

    @helper
    async def random_cex_withdraw(self, dapp_id):
        await self.cex_multi_withdraw(dapp_id, random_network=True)

        return True

    @helper
    @gas_checker
    async def smart_random_approve(self):
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

        client, index = await self.balance_searcher(STARGATE_CHAINS, STARGATE_TOKENS)

        self.logger_msg(*self.client.acc_info, msg=f"Detected balance in {client.network.name}", type_msg='success')

        network_name = client.network.name

        all_network_contracts = {
            name: contracts[network_name]['router']
            for name, contracts in all_contracts.items()
            if contracts.get(network_name)
        }

        approve_contracts = [(k, v) for k, v in all_network_contracts.items()]
        contract_name, approve_contract = random.choice(approve_contracts)
        native = ['ETH', 'WETH', 'BNB', 'MATIC', 'AVAX', 'WMATIC']
        token_contract = random.choice([i for i in list(TOKENS_PER_CHAIN[network_name].items()) if i not in native])
        amount = random.uniform(1, 10000)
        amount_in_wei = int(amount * 10 ** await client.get_decimals(token_contract[0]))

        message = f"Approve {amount:.4f} {token_contract[0]} for {contract_name}"
        self.logger_msg(*client.acc_info, msg=message)
        result = await client.check_for_approved(token_contract[1], approve_contract, amount_in_wei,
                                                 without_bal_check=True)

        await client.session.close()

        return result
