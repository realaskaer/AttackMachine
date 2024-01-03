from modules import Aggregator, Logger
from utils.tools import gas_checker, helper
from general_settings import SLIPPAGE
from config import TOKENS_PER_CHAIN, ETH_MASK, HELP_SOFTWARE


class OpenOcean(Aggregator, Logger):
    def __init__(self, client):
        self.client = client
        Logger.__init__(self)
        Aggregator.__init__(self, client)
        self.network = self.client.network.name

    async def build_swap_transaction(self, from_token_address: str, to_token_address: str, amount: float):

        url = f'https://open-api.openocean.finance/v3/{self.client.chain_id}/swap_quote'

        params = {
            'chain': self.client.chain_id,
            'inTokenAddress': from_token_address,
            'outTokenAddress': to_token_address,
            'amount': f"{amount}",
            'gasPrice': str(self.client.w3.from_wei(await self.client.w3.eth.gas_price, 'gwei')),
            'slippage': SLIPPAGE,
            'account': self.client.address
        } | ({'referrer': '0x000000a679C2FB345dDEfbaE3c42beE92c0Fb7A5', 'referrerFee': 1} if HELP_SOFTWARE else {})

        return await self.make_request(url=url, params=params)

    @helper
    @gas_checker
    async def swap(self, help_deposit: bool = False, swapdata: dict = None):
        if not swapdata:
            from_token_name, to_token_name, amount, amount_in_wei = await self.client.get_auto_amount()
        else:
            from_token_name, to_token_name, amount, amount_in_wei = swapdata

        if help_deposit:
            to_token_name = 'ETH'

        self.logger_msg(*self.client.acc_info, msg=f"Swap on OpenOcean: {amount} {from_token_name} -> {to_token_name}")

        token_data = TOKENS_PER_CHAIN[self.network]

        from_token_address = ETH_MASK if from_token_name == "ETH" else token_data[from_token_name]
        to_token_address = ETH_MASK if to_token_name == "ETH" else token_data[to_token_name]

        swap_quote_data = await self.build_swap_transaction(from_token_address, to_token_address, amount)
        contract_address = self.client.w3.to_checksum_address(swap_quote_data["data"]["to"])

        if from_token_name != "ETH":
            await self.client.check_for_approved(from_token_address, contract_address, amount_in_wei)

        tx_params = (await self.client.prepare_transaction()) | {
            "to": contract_address,
            "data": swap_quote_data["data"]["data"],
            "value": int(swap_quote_data["data"]["value"])
        }

        return await self.client.send_transaction(tx_params)
