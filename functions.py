import random

from modules import *
from utils.networks import *
from config import OKX_WRAPED_ID, LAYERZERO_WRAPED_NETWORKS
from settings import (LAYERSWAP_CHAIN_ID_FROM, ORBITER_CHAIN_ID_FROM, RHINO_CHAIN_ID_FROM,
                      OKX_DEPOSIT_NETWORK, SOURCE_CHAIN_MERKLY, SOURCE_CHAIN_ZERIUS)


async def get_client(account_number, private_key, network, proxy):
    client_instance = Client(account_number, private_key, network, proxy)
    return client_instance


def get_network_by_chain_id(chain_id):
    return {
        1: Arbitrum,
        2: Arbitrum_nova,
        3: Base,
        4: Linea,
        5: Manta,
        6: Polygon,
        7: Optimism,
        8: ScrollRPC,
        9: Polygon_ZKEVM,
        10: zkSyncEra,
        11: Zora,
        12: zkSyncEra,
        13: Ethereum
    }[chain_id]


async def swap_woofi(account_number, private_key, network, proxy):
    worker = WooFi(await get_client(account_number, private_key, network, proxy))
    await worker.swap()


async def swap_syncswap(account_number, private_key, network, proxy):
    worker = SyncSwap(await get_client(account_number, private_key, network, proxy))
    await worker.swap()


async def add_liquidity_syncswap(account_number, private_key, network, proxy):
    worker = SyncSwap(await get_client(account_number, private_key, network, proxy))
    await worker.add_liquidity()


async def add_liquidity_mute(account_number, private_key, network, proxy):
    worker = Mute(await get_client(account_number, private_key, network, proxy))
    await worker.add_liquidity()


async def add_liquidity_maverick(account_number, private_key, network, proxy):
    worker = Maverick(await get_client(account_number, private_key, network, proxy))
    await worker.add_liquidity()


async def withdraw_liquidity_maverick(account_number, private_key, network, proxy):
    worker = Maverick(await get_client(account_number, private_key, network, proxy))
    await worker.withdraw_liquidity()


async def withdraw_liquidity_mute(account_number, private_key, network, proxy):
    worker = Mute(await get_client(account_number, private_key, network, proxy))
    await worker.withdraw_liquidity()


async def withdraw_liquidity_syncswap(account_number, private_key, network, proxy):
    worker = SyncSwap(await get_client(account_number, private_key, network, proxy))
    await worker.withdraw_liquidity()


async def send_message_dmail(account_number, private_key, network, proxy):
    worker = Dmail(await get_client(account_number, private_key, network, proxy))
    await worker.send_message()


async def bridge_txsync(account_number, private_key, _, proxy):
    network = get_network_by_chain_id(13)
    worker = ZkSync(await get_client(account_number, private_key, network, proxy))
    await worker.deposit()


async def transfer_eth(account_number, private_key, network, proxy):
    worker = ZkSync(await get_client(account_number, private_key, network, proxy))
    await worker.transfer_eth()


async def transfer_eth_to_myself(account_number, private_key, network, proxy):
    worker = ZkSync(await get_client(account_number, private_key, network, proxy))
    await worker.transfer_eth_to_myself()


async def withdraw_txsync(account_number, private_key, network, proxy):
    worker = ZkSync(await get_client(account_number, private_key, network, proxy))
    await worker.withdraw()


async def wrap_eth(account_number, private_key, network, proxy):
    worker = ZkSync(await get_client(account_number, private_key, network, proxy))
    await worker.wrap_eth()


async def unwrap_eth(account_number, private_key, network, proxy):
    wrap = ZkSync(await get_client(account_number, private_key, network, proxy))
    await wrap.unwrap_eth()


async def deploy_contract(account_number, private_key, network, proxy):
    wrap = ZkSync(await get_client(account_number, private_key, network, proxy))
    await wrap.deploy_contract()


# async  def mint_deployed_token(account_number, private_key, network, proxy, *args, **kwargs):
#     mint = ZkSync(account_number, private_key, network, proxy)
#     await mint.mint_token()


async def swap_odos(account_number, private_key, network, proxy, **kwargs):
    worker = Odos(await get_client(account_number, private_key, network, proxy))
    await worker.swap(**kwargs)


async def swap_xyfinance(account_number, private_key, network, proxy):
    worker = Odos(await get_client(account_number, private_key, network, proxy))
    await worker.swap()


async def swap_rango(account_number, private_key, network, proxy):
    worker = Rango(await get_client(account_number, private_key, network, proxy))
    await worker.swap()


async def swap_openocean(account_number, private_key, network, proxy):
    worker = OpenOcean(await get_client(account_number, private_key, network, proxy))
    await worker.swap()


async def swap_oneinch(account_number, private_key, network, proxy, **kwargs):
    worker = OneInch(await get_client(account_number, private_key, network, proxy))
    await worker.swap(**kwargs)


async def swap_izumi(account_number, private_key, network, proxy):
    worker = Izumi(await get_client(account_number, private_key, network, proxy))
    await worker.swap()


async def swap_maverick(account_number, private_key, network, proxy):
    worker = Maverick(await get_client(account_number, private_key, network, proxy))
    await worker.swap()


async def swap_zkswap(account_number, private_key, network, proxy):
    worker = ZkSwap(await get_client(account_number, private_key, network, proxy))
    await worker.swap()


async def swap_spacefi(account_number, private_key, network, proxy):
    worker = SpaceFi(await get_client(account_number, private_key, network, proxy))
    await worker.swap()


async def swap_mute(account_number, private_key, network, proxy):
    worker = Mute(await get_client(account_number, private_key, network, proxy))
    await worker.swap()


async def swap_vesync(account_number, private_key, network, proxy):
    worker = VeSync(await get_client(account_number, private_key, network, proxy))
    await worker.swap()


async def swap_pancake(account_number, private_key, network, proxy):
    worker = PancakeSwap(await get_client(account_number, private_key, network, proxy))
    await worker.swap()


async def swap_velocore(account_number, private_key, network, proxy):
    worker = Velocore(await get_client(account_number, private_key, network, proxy))
    await worker.swap()


async def deposit_eralend(account_number, private_key, network, proxy):
    worker = EraLend(await get_client(account_number, private_key, network, proxy))
    await worker.deposit()


async def withdraw_eralend(account_number, private_key, network, proxy):
    worker = EraLend(await get_client(account_number, private_key, network, proxy))
    await worker.withdraw()


async def enable_collateral_eralend(account_number, private_key, network, proxy):
    worker = EraLend(await get_client(account_number, private_key, network, proxy))
    await worker.enable_collateral()


async def disable_collateral_eralend(account_number, private_key, network, proxy):
    worker = EraLend(await get_client(account_number, private_key, network, proxy))
    await worker.disable_collateral()


async def deposit_reactorfusion(account_number, private_key, network, proxy):
    worker = ReactorFusion(await get_client(account_number, private_key, network, proxy))
    await worker.deposit()


async def withdraw_reactorfusion(account_number, private_key, network, proxy):
    worker = ReactorFusion(await get_client(account_number, private_key, network, proxy))
    await worker.withdraw()


async def enable_collateral_reactorfusion(account_number, private_key, network, proxy):
    worker = ReactorFusion(await get_client(account_number, private_key, network, proxy))
    await worker.enable_collateral()


async def disable_collateral_reactorfusion(account_number, private_key, network, proxy):
    worker = ReactorFusion(await get_client(account_number, private_key, network, proxy))
    await worker.disable_collateral()


async def deposit_basilisk(account_number, private_key, network, proxy):
    worker = Basilisk(await get_client(account_number, private_key, network, proxy))
    await worker.deposit()


async def withdraw_basilisk(account_number, private_key, network, proxy):
    worker = Basilisk(await get_client(account_number, private_key, network, proxy))
    await worker.withdraw()


async def enable_collateral_basilisk(account_number, private_key, network, proxy):
    worker = Basilisk(await get_client(account_number, private_key, network, proxy))
    await worker.enable_collateral()


async def disable_collateral_basilisk(account_number, private_key, network, proxy):
    worker = Basilisk(await get_client(account_number, private_key, network, proxy))
    await worker.disable_collateral()


async def deposit_zerolend(account_number, private_key, network, proxy):
    worker = ZeroLend(await get_client(account_number, private_key, network, proxy))
    await worker.deposit()


async def withdraw_zerolend(account_number, private_key, network, proxy):
    worker = ZeroLend(await get_client(account_number, private_key, network, proxy))
    await worker.withdraw()


async def enable_collateral_zerolend(account_number, private_key, network, proxy):
    worker = ZeroLend(await get_client(account_number, private_key, network, proxy))
    await worker.enable_collateral()


async def disable_collateral_zerolend(account_number, private_key, network, proxy):
    worker = ZeroLend(await get_client(account_number, private_key, network, proxy))
    await worker.disable_collateral()


async def mint_domain_zns(account_number, private_key, network, proxy):
    worker = ZkSyncNameService(await get_client(account_number, private_key, network, proxy))
    await worker.mint()


async def mint_domain_ens(account_number, private_key, network, proxy):
    worker = EraDomainService(await get_client(account_number, private_key, network, proxy))
    await worker.mint()


async def bridge_layerswap(account_number, private_key, _, proxy, **kwargs):
    if kwargs.get('help_okx') is True:
        chain_from_id = 10
    else:
        chain_from_id = random.choice(LAYERSWAP_CHAIN_ID_FROM)
    network = get_network_by_chain_id(chain_from_id)

    worker = LayerSwap(await get_client(account_number, private_key, network, proxy))
    await worker.bridge(chain_from_id,  **kwargs)


async def bridge_orbiter(account_number, private_key, _, proxy, **kwargs):
    if kwargs.get('help_okx') is True:
        chain_from_id = 10
    else:
        chain_from_id = random.choice(ORBITER_CHAIN_ID_FROM)
    network = get_network_by_chain_id(chain_from_id)

    worker = Orbiter(await get_client(account_number, private_key, network, proxy))
    await worker.bridge(chain_from_id, **kwargs)


async def bridge_rhino(account_number, private_key, _, proxy, **kwargs):
    if kwargs.get('help_okx') is True:
        chain_from_id = 10
    else:
        chain_from_id = random.choice(RHINO_CHAIN_ID_FROM)
    network = get_network_by_chain_id(chain_from_id)

    worker = Rhino(await get_client(account_number, private_key, network, proxy))
    await worker.bridge(chain_from_id, **kwargs)


async def refuel_merkly(account_number, private_key, _, proxy):
    chain_from_id = LAYERZERO_WRAPED_NETWORKS[random.choice(SOURCE_CHAIN_MERKLY)]
    network = get_network_by_chain_id(chain_from_id)

    worker = Merkly(await get_client(account_number, private_key, network, proxy))
    await worker.refuel(chain_from_id)


async def mint_zerius(account_number, private_key, _, proxy):
    chain_from_id = LAYERZERO_WRAPED_NETWORKS[random.choice(SOURCE_CHAIN_ZERIUS)]
    network = get_network_by_chain_id(chain_from_id)

    worker = Zerius(await get_client(account_number, private_key, network, proxy), chain_from_id)
    await worker.mint()


async def bridge_zerius(account_number, private_key, _, proxy):
    chain_from_id = LAYERZERO_WRAPED_NETWORKS[random.choice(SOURCE_CHAIN_ZERIUS)]
    network = get_network_by_chain_id(chain_from_id)

    worker = Zerius(await get_client(account_number, private_key, network, proxy), chain_from_id)
    await worker.bridge()


async def refuel_bungee(account_number, private_key, network, proxy):
    worker = Bungee(await get_client(account_number, private_key, network, proxy))
    await worker.refuel()


async def mint_mailzero(account_number, private_key, network, proxy):
    worker = MailZero(await get_client(account_number, private_key, network, proxy))
    await worker.mint()


async def send_message_l2telegraph(account_number, private_key, network, proxy):
    worker = L2Telegraph(await get_client(account_number, private_key, network, proxy))
    await worker.send_message()


async def mint_and_bridge_l2telegraph(account_number, private_key, network, proxy):
    worker = L2Telegraph(await get_client(account_number, private_key, network, proxy))
    await worker.mint_and_bridge()


async def mint_tevaera(account_number, private_key, network, proxy):
    worker = Tevaera(await get_client(account_number, private_key, network, proxy))
    await worker.mint()


async def create_omnisea(account_number, private_key, network, proxy):
    worker = Omnisea(await get_client(account_number, private_key, network, proxy))
    await worker.create()


async def create_safe(account_number, private_key, network, proxy):
    worker = GnosisSafe(await get_client(account_number, private_key, network, proxy))
    await worker.create()


async def okx_withdraw(account_number, private_key, network, proxy):
    worker = OKX(await get_client(account_number, private_key, network, proxy))
    await worker.withdraw()


async def okx_deposit(account_number, private_key, _, proxy):
    network = get_network_by_chain_id(OKX_WRAPED_ID[OKX_DEPOSIT_NETWORK])

    worker = OKX(await get_client(account_number, private_key, network, proxy))
    await worker.deposit()


async def okx_collect_from_sub(account_number, private_key, network, proxy):
    worker = OKX(await get_client(account_number, private_key, network, proxy))
    await worker.collect_from_sub()
