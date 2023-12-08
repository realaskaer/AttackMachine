import random

from config import ETH_PRICE, TOKENS_PER_CHAIN
from modules import Logger, Aggregator
from settings import GLOBAL_NETWORK, OKX_BALANCE_WANTED
from utils.tools import helper, gas_checker


class Custom(Logger, Aggregator):
    def __init__(self, client):
        Logger.__init__(self)
        Aggregator.__init__(self, client)

    async def swap(self):
        pass

    async def collect_eth_util(self):
        from functions import swap_odos, swap_oneinch, swap_openocean, swap_xyfinance, swap_rango, swap_avnu

        self.logger_msg(*self.client.acc_info, msg=f"Stark collecting tokens to ETH")

        func = {
            3: [swap_odos, swap_oneinch, swap_openocean, swap_xyfinance],
            4: [swap_rango, swap_openocean, swap_xyfinance],
            8: [swap_openocean, swap_xyfinance],
            9: [swap_avnu],
            11: [swap_openocean, swap_xyfinance, swap_odos, swap_oneinch]
        }[GLOBAL_NETWORK]

        wallet_balance = {k: await self.client.get_token_balance(k, False)
                          for k, v in TOKENS_PER_CHAIN[self.client.network.name].items()}
        valid_wallet_balance = {k: v[1] for k, v in wallet_balance.items() if v[0] != 0}

        if len(valid_wallet_balance.values()) > 1:

            for token_name, token_balance in valid_wallet_balance.items():
                if token_name != 'ETH':
                    amount_in_wei = wallet_balance[token_name][0]
                    amount = float(f"{(amount_in_wei / 10 ** await self.client.get_decimals(token_name)):.5f}")
                    if amount > 1:
                        from_token_name, to_token_name = token_name, 'ETH'
                        data = from_token_name, to_token_name, amount, amount_in_wei
                        while True:
                            result = False
                            module_func = random.choice(func)
                            try:
                                self.logger_msg(*self.client.acc_info, msg=f'Launching swap module', type_msg='warning')
                                result = await module_func(self.client.account_name, self.client.private_key,
                                                           self.client.network, self.client.proxy_init, swapdata=data)
                            except:
                                pass
                            if result:
                                break
                    else:
                        self.logger_msg(*self.client.acc_info, msg=f"{token_name} balance < 1$")

            return True
        else:
            raise RuntimeError('Account balance already in ETH!')

    @helper
    @gas_checker
    async def collect_eth(self):
        await self.collect_eth_util()

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
        raise RuntimeError('Account has enough tokens on balance!')
