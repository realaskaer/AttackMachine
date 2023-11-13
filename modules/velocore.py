# from time import time
# from modules import DEX
# from utils.tools import gas_checker, repeater
# from settings import SLIPPAGE_PERCENT
# from config import (
#     VELOCORE_CONTRACTS,
#     VELOCORE_ROUTER_ABI,
#     ZKSYNC_TOKENS,
#     ZERO_ADDRESS
# )
#
#
# class Velocore(DEX):
#     def __init__(self, client):
#         self.client = client
#
#         self.vault_contract = self.client.get_contract(VELOCORE_CONTRACTS['router'], VELOCORE_ROUTER_ABI)
#         self.swap_helper_contract = self.client.get_contract(VELOCORE_CONTRACTS['swap_helper'], VELOCORE_ROUTER_ABI)
#
#     def to_token(self, spec: str, id: int, addr: str):
#         return self.client.w3.solidity_keccak(["uint8", "uint120", "address"],
#                                               [["erc20", "erc721", "erc1155"].index(spec), id, addr])
#
#     async def get_out_data(self, from_token_address: str, to_token_address: str, amount_in_wei: int):
#         min_amount_out = await self.swap_helper_contract.functions.getAmountsOut(
#             amount_in_wei,
#             [
#                 from_token_address,
#                 to_token_address
#             ]
#         ).call()
#
#         return int(min_amount_out - (min_amount_out / 100 * SLIPPAGE_PERCENT))
#
#     @repeater
#     @gas_checker
#     async def swap(self):
#
#         from_token_name, to_token_name, amount, amount_in_wei = 'ETH', 'USDT', 0.01, 10000000000000000 #await self.client.get_auto_amount()
#
#         self.client.logger.info(
#             f'{self.client.info} Swap on Velocore: {amount} {from_token_name} -> {to_token_name}')
#
#         from_token_address = ZERO_ADDRESS if from_token_name == "ETH" else ZKSYNC_TOKENS[from_token_name]
#         to_token_address = ZERO_ADDRESS if to_token_name == "ETH" else ZKSYNC_TOKENS[to_token_name]
#
#         if from_token_name != 'ETH':
#             await self.client.check_for_approved(from_token_address, VELOCORE_CONTRACTS['router'], amount_in_wei)
#
#         tx_params = await self.client.prepare_transaction(value=amount_in_wei if from_token_name == 'ETH' else 0)
#         deadline = int(time()) + 1800
#         min_amount_out = await self.get_out_data(from_token_address, to_token_address, amount_in_wei)
#         print(min_amount_out)
#
#         full_data = (
#             min_amount_out,
#             [
#                 [
#                     from_token_address,
#                     to_token_address,
#                     False
#                 ]
#             ],
#             self.client.address,
#             deadline
#         )
#
#         if from_token_name == 'ETH':
#             transaction = await self.vault_contract.functions.swapExactETHForTokens(
#                 *full_data
#             ).build_transaction(tx_params)
#         elif to_token_name == 'ETH':
#             transaction = await self.vault_contract.functions.swapExactTokensForETH(
#                 amount_in_wei,
#                 *full_data
#             ).build_transaction(tx_params)
#         else:
#             raise RuntimeError('Not support Stable pools!')
#
#         print(transaction)
#         return
#         tx_hash = await self.client.send_transaction(transaction)
#
#         return await self.client.verify_transaction(tx_hash)