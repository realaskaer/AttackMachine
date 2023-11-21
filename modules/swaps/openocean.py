from modules import Aggregator
from utils.tools import gas_checker, repeater
from settings import SLIPPAGE
from config import OPENOCEAN_CONTRACT, TOKENS_PER_CHAIN, ETH_MASK, HELP_SOFTWARE


class OpenOcean(Aggregator):
    async def build_swap_transaction(self, from_token_address: str, to_token_address: str, amount: float):

        url = f'https://open-api.openocean.finance/v3/{self.client.chain_id}/swap_quote'

        params = {
            'chain': self.client.chain_id,
            'inTokenAddress': from_token_address,
            'outTokenAddress': to_token_address,
            'amount': amount,
            'gasPrice': str(self.client.w3.from_wei(await self.client.w3.eth.gas_price, 'gwei')),
            'slippage': SLIPPAGE,
            'account': self.client.address
        } | {'referrer': '0x000000a679C2FB345dDEfbaE3c42beE92c0Fb7A5', 'referrerFee': 1} if HELP_SOFTWARE else {}

        return await self.make_request(url=url, params=params)

    @repeater
    @gas_checker
    async def swap(self):

        (from_token_name, to_token_name,
         amount, amount_in_wei) = await self.client.get_auto_amount(class_name='OpenOcean')

        self.client.logger.info(
            f'{self.client.info} Swap on OpenOcean: {amount} {from_token_name} -> {to_token_name}')

        token_data = TOKENS_PER_CHAIN[self.client.network.name]

        from_token_address = ETH_MASK if from_token_name == "ETH" else token_data[from_token_name]
        to_token_address = ETH_MASK if to_token_name == "ETH" else token_data[to_token_name]

        swap_quote_data = await self.build_swap_transaction(from_token_address, to_token_address, amount)

        if from_token_address != ETH_MASK:
            await self.client.check_for_approved(from_token_address, OPENOCEAN_CONTRACT["router"], amount_in_wei)

        tx_params = (await self.client.prepare_transaction()) | {
            "to": swap_quote_data["data"]["to"],
            "data": swap_quote_data["data"]["data"],
            "value": int(swap_quote_data["data"]["value"])
        }

        return await self.client.send_transaction(tx_params)
