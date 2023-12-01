import random

from modules import *
from utils.networks import *
from config import OKX_WRAPED_ID, LAYERZERO_WRAPED_NETWORKS
from settings import (BRIDGE_CHAIN_ID_FROM, OKX_DEPOSIT_NETWORK, SOURCE_CHAIN_MERKLY,
                      SOURCE_CHAIN_ZERIUS, GLOBAL_NETWORK)


def get_client(account_number, private_key, network, proxy, bridge_from_evm:bool = False) -> Client | StarknetClient:
    if GLOBAL_NETWORK != 9 or bridge_from_evm:
        return Client(account_number, private_key, network, proxy)
    return StarknetClient(account_number, private_key, network, proxy)


def get_interface_by_chain_id(chain_id, deposit_module:bool = False):
    return {
        3: Base,
        4: Linea,
        8: Scroll,
        9: StarknetEVM if deposit_module else Starknet,
        11: ZkSync,
    }[chain_id]


def get_network_by_chain_id(chain_id):
    return {
        1: ArbitrumRPC,
        2: Arbitrum_novaRPC,
        3: BaseRPC,
        4: LineaRPC,
        5: MantaRPC,
        6: PolygonRPC,
        7: OptimismRPC,
        8: ScrollRPC,
        9: StarknetRPC,
        10: Polygon_ZKEVM_RPC,
        11: zkSyncEraRPC,
        12: ZoraRPC,
        13: zkSyncEraRPC,
        14: EthereumRPC,
    }[chain_id]


def get_key_by_id_from(args, chain_from_id):
    private_keys = args[0].get('stark_key'), args[0].get('evm_key')
    current_key = private_keys[1]
    if chain_from_id == 9:
        current_key = private_keys[0]
    return current_key


async def swap_woofi(account_number, private_key, network, proxy):
    worker = WooFi(get_client(account_number, private_key, network, proxy))
    return await worker.swap()


async def swap_syncswap(account_number, private_key, network, proxy):
    worker = SyncSwap(get_client(account_number, private_key, network, proxy))
    return await worker.swap()


async def add_liquidity_syncswap(account_number, private_key, network, proxy):
    worker = SyncSwap(get_client(account_number, private_key, network, proxy))
    return await worker.add_liquidity()


async def add_liquidity_mute(account_number, private_key, network, proxy):
    worker = Mute(get_client(account_number, private_key, network, proxy))
    return await worker.add_liquidity()


async def add_liquidity_maverick(account_number, private_key, network, proxy):
    worker = Maverick(get_client(account_number, private_key, network, proxy))
    return await worker.add_liquidity()


async def withdraw_liquidity_maverick(account_number, private_key, network, proxy):
    worker = Maverick(get_client(account_number, private_key, network, proxy))
    return await worker.withdraw_liquidity()


async def withdraw_liquidity_mute(account_number, private_key, network, proxy):
    worker = Mute(get_client(account_number, private_key, network, proxy))
    return await worker.withdraw_liquidity()


async def withdraw_liquidity_syncswap(account_number, private_key, network, proxy):
    worker = SyncSwap(get_client(account_number, private_key, network, proxy))
    return await worker.withdraw_liquidity()


async def send_message_dmail(account_number, private_key, _, proxy):
    network = get_network_by_chain_id(GLOBAL_NETWORK)
    worker = Dmail(get_client(account_number, private_key, network, proxy))
    return await worker.send_message()


async def bridge_native(account_number, private_key, _, proxy):
    network = get_network_by_chain_id(14)
    blockchain = get_interface_by_chain_id(GLOBAL_NETWORK, deposit_module=True)

    worker = blockchain(get_client(account_number, private_key, network, proxy))
    return await worker.deposit()


async def transfer_eth(account_number, private_key, network, proxy):
    blockchain = get_interface_by_chain_id(GLOBAL_NETWORK)

    worker = blockchain(get_client(account_number, private_key, network, proxy))
    return await worker.transfer_eth()


async def transfer_eth_to_myself(account_number, private_key, network, proxy):
    blockchain = get_interface_by_chain_id(GLOBAL_NETWORK)

    worker = blockchain(get_client(account_number, private_key, network, proxy))
    return await worker.transfer_eth_to_myself()


async def withdraw_native_bridge(account_number, private_key, network, proxy):
    worker = ZkSync(get_client(account_number, private_key, network, proxy))
    return await worker.withdraw()


async def wrap_eth(account_number, private_key, network, proxy):
    worker = ZkSync(get_client(account_number, private_key, network, proxy))
    return await worker.wrap_eth()


async def unwrap_eth(account_number, private_key, network, proxy):
    wrap = ZkSync(get_client(account_number, private_key, network, proxy))
    return await wrap.unwrap_eth()


async def deploy_contract(account_number, private_key, network, proxy):
    wrap = ZkSync(get_client(account_number, private_key, network, proxy))
    return await wrap.deploy_contract()


# async  def mint_deployed_token(account_number, private_key, network, proxy, *args, **kwargs):
#     mint = ZkSync(account_number, private_key, network, proxy)
#     await mint.mint_token()


async def swap_odos(account_number, private_key, network, proxy, **kwargs):
    worker = Odos(get_client(account_number, private_key, network, proxy))
    return await worker.swap(**kwargs)


async def swap_xyfinance(account_number, private_key, network, proxy, **kwargs):
    worker = XYfinance(get_client(account_number, private_key, network, proxy))
    return await worker.swap(**kwargs)


async def swap_rango(account_number, private_key, network, proxy, **kwargs):
    worker = Rango(get_client(account_number, private_key, network, proxy))
    return await worker.swap(**kwargs)


async def swap_openocean(account_number, private_key, network, proxy, **kwargs):
    worker = OpenOcean(get_client(account_number, private_key, network, proxy))
    return await worker.swap(**kwargs)


async def swap_oneinch(account_number, private_key, network, proxy, **kwargs):
    worker = OneInch(get_client(account_number, private_key, network, proxy))
    return await worker.swap(**kwargs)


async def swap_izumi(account_number, private_key, network, proxy):
    worker = Izumi(get_client(account_number, private_key, network, proxy))
    return await worker.swap()


async def swap_maverick(account_number, private_key, network, proxy):
    worker = Maverick(get_client(account_number, private_key, network, proxy))
    return await worker.swap()


async def swap_zkswap(account_number, private_key, network, proxy):
    worker = ZkSwap(get_client(account_number, private_key, network, proxy))
    return await worker.swap()


async def swap_spacefi(account_number, private_key, network, proxy):
    worker = SpaceFi(get_client(account_number, private_key, network, proxy))
    return await worker.swap()


async def swap_mute(account_number, private_key, network, proxy):
    worker = Mute(get_client(account_number, private_key, network, proxy))
    return await worker.swap()


async def swap_vesync(account_number, private_key, network, proxy):
    worker = VeSync(get_client(account_number, private_key, network, proxy))
    return await worker.swap()


async def swap_pancake(account_number, private_key, network, proxy):
    worker = PancakeSwap(get_client(account_number, private_key, network, proxy))
    return await worker.swap()


async def swap_velocore(account_number, private_key, network, proxy):
    worker = Velocore(get_client(account_number, private_key, network, proxy))
    return await worker.swap()


async def deposit_eralend(account_number, private_key, network, proxy):
    worker = EraLend(get_client(account_number, private_key, network, proxy))
    return await worker.deposit()


async def withdraw_eralend(account_number, private_key, network, proxy):
    worker = EraLend(get_client(account_number, private_key, network, proxy))
    return await worker.withdraw()


async def enable_collateral_eralend(account_number, private_key, network, proxy):
    worker = EraLend(get_client(account_number, private_key, network, proxy))
    return await worker.enable_collateral()


async def disable_collateral_eralend(account_number, private_key, network, proxy):
    worker = EraLend(get_client(account_number, private_key, network, proxy))
    return await worker.disable_collateral()


async def deposit_reactorfusion(account_number, private_key, network, proxy):
    worker = ReactorFusion(get_client(account_number, private_key, network, proxy))
    return await worker.deposit()


async def withdraw_reactorfusion(account_number, private_key, network, proxy):
    worker = ReactorFusion(get_client(account_number, private_key, network, proxy))
    return await worker.withdraw()


async def enable_collateral_reactorfusion(account_number, private_key, network, proxy):
    worker = ReactorFusion(get_client(account_number, private_key, network, proxy))
    return await worker.enable_collateral()


async def disable_collateral_reactorfusion(account_number, private_key, network, proxy):
    worker = ReactorFusion(get_client(account_number, private_key, network, proxy))
    return await worker.disable_collateral()


async def deposit_basilisk(account_number, private_key, network, proxy):
    worker = Basilisk(get_client(account_number, private_key, network, proxy))
    return await worker.deposit()


async def withdraw_basilisk(account_number, private_key, network, proxy):
    worker = Basilisk(get_client(account_number, private_key, network, proxy))
    return await worker.withdraw()


async def enable_collateral_basilisk(account_number, private_key, network, proxy):
    worker = Basilisk(get_client(account_number, private_key, network, proxy))
    return await worker.enable_collateral()


async def disable_collateral_basilisk(account_number, private_key, network, proxy):
    worker = Basilisk(get_client(account_number, private_key, network, proxy))
    return await worker.disable_collateral()


async def deposit_zerolend(account_number, private_key, network, proxy):
    worker = ZeroLend(get_client(account_number, private_key, network, proxy))
    return await worker.deposit()


async def withdraw_zerolend(account_number, private_key, network, proxy):
    worker = ZeroLend(get_client(account_number, private_key, network, proxy))
    return await worker.withdraw()


async def mint_domain_zns(account_number, private_key, network, proxy):
    worker = ZkSyncNameService(get_client(account_number, private_key, network, proxy))
    return await worker.mint()


async def mint_domain_ens(account_number, private_key, network, proxy):
    worker = EraDomainService(get_client(account_number, private_key, network, proxy))
    return await worker.mint()


async def bridge_layerswap(account_number, _, __, proxy, *args, **kwargs):
    if kwargs.get('help_okx') is True:
        chain_from_id = GLOBAL_NETWORK
    else:
        chain_from_id = random.choice(BRIDGE_CHAIN_ID_FROM)
    network = get_network_by_chain_id(chain_from_id)

    bridge_from_evm = True if 9 not in BRIDGE_CHAIN_ID_FROM else False
    private_key = get_key_by_id_from(args, chain_from_id)

    worker = LayerSwap(get_client(account_number, private_key, network, proxy, bridge_from_evm))
    return await worker.bridge(chain_from_id, *args, **kwargs)


async def bridge_orbiter(account_number, _, __, proxy, *args, **kwargs):
    if kwargs.get('help_okx') is True:
        chain_from_id = GLOBAL_NETWORK
    else:
        chain_from_id = random.choice(BRIDGE_CHAIN_ID_FROM)
    network = get_network_by_chain_id(chain_from_id)

    bridge_from_evm = True if 9 not in BRIDGE_CHAIN_ID_FROM else False
    private_key = get_key_by_id_from(args, chain_from_id)

    worker = Orbiter(get_client(account_number, private_key, network, proxy, bridge_from_evm))
    return await worker.bridge(chain_from_id, *args, **kwargs)


async def bridge_rhino(account_number, _, __, proxy, *args, **kwargs):
    if kwargs.get('help_okx') is True:
        chain_from_id = GLOBAL_NETWORK
    else:
        chain_from_id = random.choice(BRIDGE_CHAIN_ID_FROM)
    network = get_network_by_chain_id(chain_from_id)

    bridge_from_evm = True if 9 not in BRIDGE_CHAIN_ID_FROM else False
    private_key = get_key_by_id_from(args, chain_from_id)

    worker = Rhino(get_client(account_number, private_key, network, proxy, bridge_from_evm))
    return await worker.bridge(chain_from_id, *args, **kwargs)


async def refuel_merkly(account_number, private_key, _, proxy):
    chain_from_id = LAYERZERO_WRAPED_NETWORKS[random.choice(SOURCE_CHAIN_MERKLY)]
    network = get_network_by_chain_id(chain_from_id)

    worker = Merkly(get_client(account_number, private_key, network, proxy))
    return await worker.refuel(chain_from_id)


async def refuel_zerius(account_number, private_key, _, proxy):
    chain_from_id = LAYERZERO_WRAPED_NETWORKS[random.choice(SOURCE_CHAIN_MERKLY)]
    network = get_network_by_chain_id(chain_from_id)

    worker = Zerius(get_client(account_number, private_key, network, proxy), chain_from_id)
    return await worker.refuel()


async def mint_zerius(account_number, private_key, _, proxy):
    chain_from_id = LAYERZERO_WRAPED_NETWORKS[random.choice(SOURCE_CHAIN_ZERIUS)]
    network = get_network_by_chain_id(chain_from_id)

    worker = Zerius(get_client(account_number, private_key, network, proxy), chain_from_id)
    return await worker.mint()


async def bridge_zerius(account_number, private_key, _, proxy):
    chain_from_id = LAYERZERO_WRAPED_NETWORKS[random.choice(SOURCE_CHAIN_ZERIUS)]
    network = get_network_by_chain_id(chain_from_id)

    worker = Zerius(get_client(account_number, private_key, network, proxy), chain_from_id)
    return await worker.bridge()


async def refuel_bungee(account_number, private_key, network, proxy):
    worker = Bungee(get_client(account_number, private_key, network, proxy))
    return await worker.refuel()


async def mint_mailzero(account_number, private_key, network, proxy):
    worker = MailZero(get_client(account_number, private_key, network, proxy))
    return await worker.mint()


async def send_message_l2telegraph(account_number, private_key, network, proxy):
    worker = L2Telegraph(get_client(account_number, private_key, network, proxy))
    return await worker.send_message()


async def mint_and_bridge_l2telegraph(account_number, private_key, network, proxy):
    worker = L2Telegraph(get_client(account_number, private_key, network, proxy))
    return await worker.mint_and_bridge()


async def mint_tevaera(account_number, private_key, network, proxy):
    worker = Tevaera(get_client(account_number, private_key, network, proxy))
    return await worker.mint()


async def create_omnisea(account_number, private_key, network, proxy):
    worker = Omnisea(get_client(account_number, private_key, network, proxy))
    return await worker.create()


async def create_safe(account_number, private_key, network, proxy):
    worker = GnosisSafe(get_client(account_number, private_key, network, proxy))
    return await worker.create()


async def okx_withdraw(account_number, private_key, network, proxy):
    worker = OKX(get_client(account_number, private_key, network, proxy))
    return await worker.withdraw()


async def okx_deposit(account_number, private_key, _, proxy):
    network = get_network_by_chain_id(OKX_WRAPED_ID[OKX_DEPOSIT_NETWORK])

    worker = OKX(get_client(account_number, private_key, network, proxy))
    return await worker.deposit()


async def okx_collect_from_sub(account_number, private_key, network, proxy):
    worker = OKX(get_client(account_number, private_key, network, proxy))
    return await worker.collect_from_sub()


async def swap_jediswap(account_number, private_key, network, proxy):
    worker = JediSwap(get_client(account_number, private_key, network, proxy))
    return await worker.swap()


async def swap_avnu(account_number, private_key, network, proxy, **kwargs):
    worker = AVNU(get_client(account_number, private_key, network, proxy))
    return await worker.swap(**kwargs)


async def swap_10kswap(account_number, private_key, network, proxy):
    worker = TenkSwap(get_client(account_number, private_key, network, proxy))
    return await worker.swap()


async def swap_sithswap(account_number, private_key, network, proxy):
    worker = SithSwap(get_client(account_number, private_key, network, proxy))
    return await worker.swap()


async def swap_myswap(account_number, private_key, network, proxy):
    worker = MySwap(get_client(account_number, private_key, network, proxy))
    return await worker.swap()


async def swap_protoss(account_number, private_key, network, proxy):
    worker = Protoss(get_client(account_number, private_key, network, proxy))
    return await worker.swap()


async def deploy_stark_wallet(account_number, private_key, network, proxy):
    worker = Starknet(get_client(account_number, private_key, network, proxy))
    return await worker.deploy_wallet()


async def upgrade_stark_wallet(account_number, private_key, network, proxy):
    worker = Starknet(get_client(account_number, private_key, network, proxy))
    return await worker.upgrade_wallet()


async def mint_starknet_identity(account_number, private_key, network, proxy):
    worker = StarknetId(get_client(account_number, private_key, network, proxy))
    return await worker.mint()


async def mint_starkstars(account_number, private_key, network, proxy):
    worker = StarkStars(get_client(account_number, private_key, network, proxy))
    return await worker.mint()


# async def deposit_carmine(account_number, private_key, network, proxy):
#     worker = Carmine(get_client(account_number, private_key, network, proxy))
#     return await worker.deposit()
#
#
# async def withdraw_carmine(account_number, private_key, network, proxy):
#     worker = Carmine(get_client(account_number, private_key, network, proxy))
#     return await worker.withdraw()


async def deposit_nostra(account_number, private_key, network, proxy):
    worker = Nostra(get_client(account_number, private_key, network, proxy))
    return await worker.deposit()


async def withdraw_nostra(account_number, private_key, network, proxy):
    worker = Nostra(get_client(account_number, private_key, network, proxy))
    return await worker.withdraw()


async def deposit_zklend(account_number, private_key, network, proxy):
    worker = ZkLend(get_client(account_number, private_key, network, proxy))
    return await worker.deposit()


async def withdraw_zklend(account_number, private_key, network, proxy):
    worker = ZkLend(get_client(account_number, private_key, network, proxy))
    return await worker.withdraw()


async def enable_collateral_zklend(account_number, private_key, network, proxy):
    worker = ZkLend(get_client(account_number, private_key, network, proxy))
    return await worker.enable_collateral()


async def disable_collateral_zklend(account_number, private_key, network, proxy):
    worker = ZkLend(get_client(account_number, private_key, network, proxy))
    return await worker.disable_collateral()


async def swap_uniswap(account_number, private_key, network, proxy):
    worker = Uniswap(get_client(account_number, private_key, network, proxy))
    return await worker.swap()


async def swap_sushiswap(account_number, private_key, network, proxy):
    worker = SushiSwap(get_client(account_number, private_key, network, proxy))
    return await worker.swap()


async def deposit_rocketsam(account_number, private_key, network, proxy):
    worker = RocketSam(get_client(account_number, private_key, network, proxy))
    return await worker.deposit()


async def withdraw_rocketsam(account_number, private_key, network, proxy):
    worker = RocketSam(get_client(account_number, private_key, network, proxy))
    return await worker.withdraw()


async def deposit_layerbank(account_number, private_key, network, proxy):
    worker = LayerBank(get_client(account_number, private_key, network, proxy))
    return await worker.deposit()


async def withdraw_layerbank(account_number, private_key, network, proxy):
    worker = LayerBank(get_client(account_number, private_key, network, proxy))
    return await worker.withdraw()


async def enable_collateral_layerbank(account_number, private_key, network, proxy):
    worker = LayerBank(get_client(account_number, private_key, network, proxy))
    return await worker.enable_collateral()


async def disable_collateral_layerbank(account_number, private_key, network, proxy):
    worker = LayerBank(get_client(account_number, private_key, network, proxy))
    return await worker.disable_collateral()


async def mint_zkstars(account_number, private_key, network, proxy):
    worker = ZkStars(get_client(account_number, private_key, network, proxy))
    return await worker.mint()


async def random_approve(account_number, private_key, network, proxy):
    worker = Starknet(get_client(account_number, private_key, network, proxy))
    return await worker.random_approve()

