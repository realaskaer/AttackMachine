from modules import *


async def swap_woofi(account_number, private_key, network, proxy):
    worker = WooFi(account_number, private_key, network, proxy)
    await worker.swap()


async def swap_syncswap(account_number, private_key, network, proxy):
    worker = SyncSwap(account_number, private_key, network, proxy)
    await worker.swap()


async def add_liquidity_syncswap(account_number, private_key, network, proxy):
    worker = SyncSwap(account_number, private_key, network, proxy)
    await worker.add_liquidity()


async def add_liquidity_mute(account_number, private_key, network, proxy):
    worker = Mute(account_number, private_key, network, proxy)
    await worker.add_liquidity()


async def add_liquidity_maverick(account_number, private_key, network, proxy):
    worker = Maverick(account_number, private_key, network, proxy)
    await worker.add_liquidity()


async def withdraw_liquidity_maverick(account_number, private_key, network, proxy):
    worker = Maverick(account_number, private_key, network, proxy)
    await worker.withdraw_liquidity()


async def withdraw_liquidity_mute(account_number, private_key, network, proxy):
    worker = Mute(account_number, private_key, network, proxy)
    await worker.withdraw_liquidity()


async def withdraw_liquidity_syncswap(account_number, private_key, network, proxy):
    worker = SyncSwap(account_number, private_key, network, proxy)
    await worker.withdraw_liquidity()


async def send_message_dmail(account_number, private_key, network, proxy):
    worker = Dmail(account_number, private_key, network, proxy)
    await worker.send_message()


async def bridge_txsync(account_number, private_key, network, proxy):
    worker = ZkSync(account_number, private_key, network, proxy)
    await worker.deposit()


async def transfer_eth(account_number, private_key, network, proxy):
    worker = ZkSync(account_number, private_key, network, proxy)
    await worker.transfer_eth()


async def transfer_eth_to_myself(account_number, private_key, network, proxy):
    worker = ZkSync(account_number, private_key, network, proxy)
    await worker.transfer_eth_to_myself()


async def withdraw_txsync(account_number, private_key, network, proxy):
    worker = ZkSync(account_number, private_key, network, proxy)
    await worker.withdraw()


async def wrap_eth(account_number, private_key, network, proxy):
    worker = ZkSync(account_number, private_key, network, proxy)
    await worker.wrap_eth()


async def unwrap_eth(account_number, private_key, network, proxy):
    wrap = ZkSync(account_number, private_key, network, proxy)
    await wrap.unwrap_eth()


# async def transfer_erc20_token(account_number, private_key, network, proxy, *args, **kwargs):
#     worker = ZkSync(account_number, private_key, network, proxy)
#     await worker.transfer_erc20_tokens(*args, **kwargs)


# async  def deploy_contract(account_number, private_key, network, proxy, *args, **kwargs):
#     wrap = ZkSync(account_number, private_key, network, proxy)
#     await wrap.deploy_contract(*args, **kwargs)


# async  def mint_deployed_token(account_number, private_key, network, proxy, *args, **kwargs):
#     mint = ZkSync(account_number, private_key, network, proxy)
#     await mint.mint_token()


async def swap_odos(account_number, private_key, network, proxy, **kwargs):
    worker = Odos(account_number, private_key, network, proxy)
    await worker.swap(**kwargs)


async def swap_rango(account_number, private_key, network, proxy):
    worker = Rango(account_number, private_key, network, proxy)
    await worker.swap()


async def swap_openocean(account_number, private_key, network, proxy):
    worker = OpenOcean(account_number, private_key, network, proxy)
    await worker.swap()


async def swap_oneinch(account_number, private_key, network, proxy, **kwargs):
    worker = OneInch(account_number, private_key, network, proxy)
    await worker.swap(**kwargs)


async def swap_izumi(account_number, private_key, network, proxy):
    worker = Izumi(account_number, private_key, network, proxy)
    await worker.swap()


async def swap_maverick(account_number, private_key, network, proxy):
    worker = Maverick(account_number, private_key, network, proxy)
    await worker.swap()


async def swap_zkswap(account_number, private_key, network, proxy):
    worker = ZkSwap(account_number, private_key, network, proxy)
    await worker.swap()


async def swap_spacefi(account_number, private_key, network, proxy):
    worker = SpaceFi(account_number, private_key, network, proxy)
    await worker.swap()


async def swap_mute(account_number, private_key, network, proxy):
    worker = Mute(account_number, private_key, network, proxy)
    await worker.swap()


async def swap_vesync(account_number, private_key, network, proxy):
    worker = VeSync(account_number, private_key, network, proxy)
    await worker.swap()


async def swap_pancake(account_number, private_key, network, proxy):
    worker = PancakeSwap(account_number, private_key, network, proxy)
    await worker.swap()


async def swap_velocore(account_number, private_key, network, proxy):
    worker = Velocore(account_number, private_key, network, proxy)
    await worker.swap()


async def deposit_eralend(account_number, private_key, network, proxy):
    worker = EraLend(account_number, private_key, network, proxy)
    await worker.deposit()


async def withdraw_eralend(account_number, private_key, network, proxy):
    worker = EraLend(account_number, private_key, network, proxy)
    await worker.withdraw()


async def enable_collateral_eralend(account_number, private_key, network, proxy):
    worker = EraLend(account_number, private_key, network, proxy)
    await worker.enable_collateral()


async def disable_collateral_eralend(account_number, private_key, network, proxy):
    worker = EraLend(account_number, private_key, network, proxy)
    await worker.disable_collateral()


async def deposit_reactorfusion(account_number, private_key, network, proxy):
    worker = ReactorFusion(account_number, private_key, network, proxy)
    await worker.deposit()


async def withdraw_reactorfusion(account_number, private_key, network, proxy):
    worker = ReactorFusion(account_number, private_key, network, proxy)
    await worker.withdraw()


async def enable_collateral_reactorfusion(account_number, private_key, network, proxy):
    worker = ReactorFusion(account_number, private_key, network, proxy)
    await worker.enable_collateral()


async def disable_collateral_reactorfusion(account_number, private_key, network, proxy):
    worker = ReactorFusion(account_number, private_key, network, proxy)
    await worker.disable_collateral()


async def deposit_basilisk(account_number, private_key, network, proxy):
    worker = Basilisk(account_number, private_key, network, proxy)
    await worker.deposit()


async def withdraw_basilisk(account_number, private_key, network, proxy):
    worker = Basilisk(account_number, private_key, network, proxy)
    await worker.withdraw()


async def enable_collateral_basilisk(account_number, private_key, network, proxy):
    worker = Basilisk(account_number, private_key, network, proxy)
    await worker.enable_collateral()


async def disable_collateral_basilisk(account_number, private_key, network, proxy):
    worker = Basilisk(account_number, private_key, network, proxy)
    await worker.disable_collateral()


async def deposit_zerolend(account_number, private_key, network, proxy):
    worker = ZeroLend(account_number, private_key, network, proxy)
    await worker.deposit()


async def withdraw_zerolend(account_number, private_key, network, proxy):
    worker = ZeroLend(account_number, private_key, network, proxy)
    await worker.withdraw()


async def enable_collateral_zerolend(account_number, private_key, network, proxy):
    worker = ZeroLend(account_number, private_key, network, proxy)
    await worker.enable_collateral()


async def disable_collateral_zerolend(account_number, private_key, network, proxy):
    worker = ZeroLend(account_number, private_key, network, proxy)
    await worker.disable_collateral()


async def mint_domain_zns(account_number, private_key, network, proxy):
    worker = ZkSyncNameService(account_number, private_key, network, proxy)
    await worker.mint_domain()


async def mint_domain_ens(account_number, private_key, network, proxy):
    worker = EraDomainService(account_number, private_key, network, proxy)
    await worker.mint_domain()


async def bridge_layerswap(account_number, private_key, network, proxy, **kwargs):
    worker = LayerSwap(account_number, private_key, network, proxy, **kwargs)
    await worker.bridge(**kwargs)


async def bridge_orbiter(account_number, private_key, network, proxy):
    worker = Orbiter(account_number, private_key, network, proxy)
    await worker.bridge()


async def refuel_merkly(account_number, private_key, network, proxy):
    worker = Merkly(account_number, private_key, network, proxy)
    await worker.refuel()


async def refuel_bungee(account_number, private_key, network, proxy):
    worker = Bungee(account_number, private_key, network, proxy)
    await worker.refuel()


async def mint_mailzero(account_number, private_key, network, proxy):
    worker = MailZero(account_number, private_key, network, proxy)
    await worker.mint()


async def send_message_l2telegraph(account_number, private_key, network, proxy):
    worker = L2Telegraph(account_number, private_key, network, proxy)
    await worker.send_message()


async def mint_and_bridge_l2telegraph(account_number, private_key, network, proxy):
    worker = L2Telegraph(account_number, private_key, network, proxy)
    await worker.mint_and_bridge()


async def mint_tevaera(account_number, private_key, network, proxy):
    worker = Tevaera(account_number, private_key, network, proxy)
    await worker.double_mint()


async def create_omnisea(account_number, private_key, network, proxy):
    worker = Omnisea(account_number, private_key, network, proxy)
    await worker.create_collection()


async def create_safe(account_number, private_key, network, proxy):
    worker = GnosisSafe(account_number, private_key, network, proxy)
    await worker.create_safe()


async def okx_withdraw(account_number, private_key, network, proxy):
    worker = OKX(account_number, private_key, network, proxy)
    await worker.withdraw()


async def okx_deposit(account_number, private_key, network, proxy):
    worker = OKX(account_number, private_key, network, proxy, switch_network=True)
    await worker.deposit()


MODULES = {
    "okx_withdraw": okx_withdraw,
    "bridge_layerswap": bridge_layerswap,
    "bridge_orbiter": bridge_orbiter,
    "bridge_txsync": bridge_txsync,
    "add_liquidity_maverick": add_liquidity_maverick,
    "add_liquidity_mute": add_liquidity_mute,
    "add_liquidity_syncswap": add_liquidity_syncswap,
    "okx_deposit": okx_deposit,
    "deposit_basilisk": deposit_basilisk,
    "deposit_eralend": deposit_eralend,
    "deposit_reactorfusion": deposit_reactorfusion,
    "deposit_zerolend": deposit_zerolend,
    "enable_collateral_basilisk": enable_collateral_basilisk,
    "enable_collateral_eralend": enable_collateral_eralend,
    "enable_collateral_reactorfusion": enable_collateral_reactorfusion,
    "enable_collateral_zerolend": enable_collateral_zerolend,
    "swap_izumi": swap_izumi,
    "swap_maverick": swap_maverick,
    "swap_mute": swap_mute,
    "swap_odos": swap_odos,
    "swap_oneinch": swap_oneinch,
    "swap_openocean": swap_openocean,
    "swap_pancake": swap_pancake,
    "swap_rango": swap_rango,
    "swap_spacefi": swap_spacefi,
    "swap_syncswap": swap_syncswap,
    "swap_velocore": swap_velocore,
    "swap_vesync": swap_vesync,
    "swap_woofi": swap_woofi,
    "swap_zkswap": swap_zkswap,
    "wrap_eth": wrap_eth,
    "create_omnisea": create_omnisea,
    "disable_collateral_basilisk": disable_collateral_basilisk,
    "disable_collateral_eralend": disable_collateral_eralend,
    "disable_collateral_reactorfusion": disable_collateral_reactorfusion,
    "disable_collateral_zerolend": disable_collateral_zerolend,
    "mint_and_bridge_l2telegraph": mint_and_bridge_l2telegraph,
    "mint_domain_ens": mint_domain_ens,
    "mint_domain_zns": mint_domain_zns,
    "mint_mailzero": mint_mailzero,
    "mint_tevaera": mint_tevaera,
    "create_safe": create_safe,
    "refuel_bungee": refuel_bungee,
    "refuel_merkly": refuel_merkly,
    "send_message_dmail": send_message_dmail,
    "send_message_l2telegraph": send_message_l2telegraph,
    "transfer_eth": transfer_eth,
    "transfer_eth_to_myself": transfer_eth_to_myself,
    "unwrap_eth": unwrap_eth,
    "withdraw_basilisk": withdraw_basilisk,
    "withdraw_eralend": withdraw_eralend,
    "withdraw_txsync": withdraw_txsync,
    "withdraw_liquidity_maverick": withdraw_liquidity_maverick,
    "withdraw_liquidity_mute": withdraw_liquidity_mute,
    "withdraw_liquidity_syncswap": withdraw_liquidity_syncswap,
    "withdraw_reactorfusion": withdraw_reactorfusion,
    "withdraw_zerolend": withdraw_zerolend,
}
