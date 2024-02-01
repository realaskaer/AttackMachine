import random

from modules import *
from utils.networks import *
from config import CEX_WRAPED_ID, LAYERZERO_WRAPED_NETWORKS
from general_settings import GLOBAL_NETWORK
from settings import (ORBITER_CHAIN_ID_FROM, LAYERSWAP_CHAIN_ID_FROM, RHINO_CHAIN_ID_FROM, ACROSS_CHAIN_ID_FROM,
                      OKX_DEPOSIT_NETWORK, SRC_CHAIN_MERKLY, SRC_CHAIN_ZERIUS, SRC_CHAIN_L2PASS,
                      SRC_CHAIN_MERKLY_WORMHOLE, SRC_CHAIN_BUNGEE, SRC_CHAIN_L2TELEGRAPH, NATIVE_CHAIN_ID_FROM,
                      L2PASS_GAS_STATION_ID_FROM, BINGX_DEPOSIT_NETWORK, BINANCE_DEPOSIT_NETWORK)


def get_client(account_number, private_key, network, proxy, bridge_from_evm:bool = False) -> Client | StarknetClient:
    if GLOBAL_NETWORK != 9 or bridge_from_evm:
        return Client(account_number, private_key, network, proxy)
    return StarknetClient(account_number, private_key, network, proxy)


def get_interface_by_chain_id(chain_id, deposit_module:bool = False):
    return {
        2: ArbitrumNova,
        3: Base,
        4: Linea,
        8: Scroll,
        9: StarknetEVM if deposit_module else Starknet,
        11: ZkSync,
        12: Zora
    }[chain_id]


def get_network_by_chain_id(chain_id):
    return {
        0: ArbitrumRPC,
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
        13: EthereumRPC,
        14: AvalancheRPC,
        15: BSC_RPC,
        16: MoonbeamRPC,
        17: HarmonyRPC,
        18: TelosRPC,
        19: CeloRPC,
        20: GnosisRPC,
        21: CoreRPC,
        22: TomoChainRPC,
        23: ConfluxRPC,
        24: OrderlyRPC,
        25: HorizenRPC,
        26: MetisRPC,
        27: AstarRPC,
        28: OpBNB_RPC,
        29: MantleRPC,
        30: MoonriverRPC,
        31: KlaytnRPC,
        32: KavaRPC,
        33: FantomRPC,
        34: AuroraRPC,
        35: CantoRPC,
        36: DFK_RPC,
        37: FuseRPC,
        38: GoerliRPC,
        39: MeterRPC,
        40: OKX_RPC,
        41: ShimmerRPC,
        42: TenetRPC,
        43: XPLA_RPC,
        44: LootChainRPC,
        45: ZKFairRPC,
        46: BeamRPC,
        47: InEVM_RPC,
    }[chain_id]


def get_key_by_id_from(args, chain_from_id):
    private_keys = args[0].get('stark_key'), args[0].get('evm_key')
    current_key = private_keys[1]
    if chain_from_id == 9:
        current_key = private_keys[0]
    return current_key


async def swap_woofi(account_number, private_key, network, proxy, **kwargs):
    worker = WooFi(get_client(account_number, private_key, network, proxy))
    return await worker.swap(**kwargs)


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


async def bridge_native(account_number, _, __, proxy, *args, **kwargs):
    network = get_network_by_chain_id(14)

    blockchain = get_interface_by_chain_id(GLOBAL_NETWORK, deposit_module=True)
    bridge_from_evm = True if GLOBAL_NETWORK == 9 else False
    private_key = get_key_by_id_from(args, 14)

    worker = blockchain(get_client(account_number, private_key, network, proxy, bridge_from_evm))
    return await worker.deposit(*args, **kwargs)


async def transfer_eth(account_number, private_key, network, proxy):
    blockchain = get_interface_by_chain_id(GLOBAL_NETWORK)

    worker = blockchain(get_client(account_number, private_key, network, proxy))
    return await worker.transfer_eth()


async def transfer_eth_to_myself(account_number, private_key, network, proxy):
    blockchain = get_interface_by_chain_id(GLOBAL_NETWORK)

    worker = blockchain(get_client(account_number, private_key, network, proxy))
    return await worker.transfer_eth_to_myself()


async def withdraw_native_bridge(account_number, _, __, proxy, *args, **kwargs):
    blockchain = get_interface_by_chain_id(GLOBAL_NETWORK)
    network = get_network_by_chain_id(GLOBAL_NETWORK)
    private_key = get_key_by_id_from(args, GLOBAL_NETWORK)

    worker = blockchain(get_client(account_number, private_key, network, proxy))
    return await worker.withdraw(*args, **kwargs)


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


async def bridge_layerswap(
        account_number, _, __, proxy, chain_from_id=LAYERSWAP_CHAIN_ID_FROM, *args, **kwargs
):
    chain_from_id = random.choice(chain_from_id)
    network = get_network_by_chain_id(chain_from_id)

    bridge_from_evm = True if 9 != chain_from_id else False
    private_key = get_key_by_id_from(args if args else kwargs['private_keys'], chain_from_id)

    worker = LayerSwap(get_client(account_number, private_key, network, proxy, bridge_from_evm))
    return await worker.bridge(chain_from_id, *args if args else kwargs['private_keys'])


async def bridge_orbiter(
        account_number, _, __, proxy, chain_from_id=ORBITER_CHAIN_ID_FROM, *args, **kwargs
):
    chain_from_id = random.choice(chain_from_id)
    network = get_network_by_chain_id(chain_from_id)

    bridge_from_evm = True if 9 != chain_from_id else False
    private_key = get_key_by_id_from(args if args else kwargs['private_keys'], chain_from_id)

    worker = Orbiter(get_client(account_number, private_key, network, proxy, bridge_from_evm))
    return await worker.bridge(chain_from_id, *args if args else kwargs['private_keys'])


async def bridge_rhino(
        account_number, _, __, proxy, chain_from_id=RHINO_CHAIN_ID_FROM, *args, **kwargs
):
    chain_from_id = random.choice(chain_from_id)
    network = get_network_by_chain_id(chain_from_id)

    bridge_from_evm = True if 9 != chain_from_id else False
    private_key = get_key_by_id_from(args if args else kwargs['private_keys'], chain_from_id)

    worker = Rhino(get_client(account_number, private_key, network, proxy, bridge_from_evm))
    return await worker.bridge(chain_from_id, *args if args else kwargs['private_keys'])


async def bridge_across(
        account_number, _, __, proxy, chain_from_id=ACROSS_CHAIN_ID_FROM, *args, **kwargs
):
    chain_from_id = random.choice(chain_from_id)
    network = get_network_by_chain_id(chain_from_id)

    bridge_from_evm = True if 9 != chain_from_id else False
    private_key = get_key_by_id_from(args if args else kwargs['private_keys'], chain_from_id)

    worker = Across(get_client(account_number, private_key, network, proxy, bridge_from_evm))
    return await worker.bridge(chain_from_id, *args if args else kwargs['private_keys'])


async def bridge_rhino_limiter(account_number, private_key, network, proxy, *args):
    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.bridge_limiter(dapp_id=1, private_keys=args)


async def bridge_layerswap_limiter(account_number, private_key, network, proxy, *args):
    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.bridge_limiter(dapp_id=2, private_keys=args)


async def bridge_orbiter_limiter(account_number, private_key, network, proxy, *args):
    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.bridge_limiter(dapp_id=3, private_keys=args)


async def bridge_across_limiter(account_number, private_key, network, proxy, *args):
    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.bridge_limiter(dapp_id=4, private_keys=args)


async def refuel_merkly(account_number, private_key, _, proxy):
    chain_from_id = LAYERZERO_WRAPED_NETWORKS[random.choice(SRC_CHAIN_MERKLY)]
    network = get_network_by_chain_id(chain_from_id)

    worker = Merkly(get_client(account_number, private_key, network, proxy))
    return await worker.refuel(chain_from_id)


async def mint_and_bridge_wormhole_nft(account_number, private_key, _, proxy):
    chain_from_id = LAYERZERO_WRAPED_NETWORKS[random.choice(SRC_CHAIN_MERKLY_WORMHOLE)]
    network = get_network_by_chain_id(chain_from_id)

    worker = Merkly(get_client(account_number, private_key, network, proxy))
    return await worker.mint_and_bridge_wormhole_nft(chain_from_id)


async def mint_and_bridge_wormhole_token(account_number, private_key, _, proxy):
    chain_from_id = LAYERZERO_WRAPED_NETWORKS[random.choice(SRC_CHAIN_MERKLY_WORMHOLE)]
    network = get_network_by_chain_id(chain_from_id)

    worker = Merkly(get_client(account_number, private_key, network, proxy))
    return await worker.mint_and_bridge_wormhole_tokens(chain_from_id)


async def refuel_l2pass(account_number, private_key, _, proxy):
    chain_from_id = LAYERZERO_WRAPED_NETWORKS[random.choice(SRC_CHAIN_L2PASS)]
    network = get_network_by_chain_id(chain_from_id)

    worker = L2Pass(get_client(account_number, private_key, network, proxy))
    return await worker.refuel(chain_from_id)


async def gas_station_l2pass(account_number, private_key, _, proxy):
    chain_from_id = LAYERZERO_WRAPED_NETWORKS[random.choice(L2PASS_GAS_STATION_ID_FROM)]
    network = get_network_by_chain_id(chain_from_id)

    worker = L2Pass(get_client(account_number, private_key, network, proxy))
    return await worker.gas_station(chain_from_id)


async def l2pass_for_refuel_attack(account_number, private_key, _, proxy, chain_from_id, **kwargs):
    network = get_network_by_chain_id(chain_from_id)

    worker = L2Pass(get_client(account_number, private_key, network, proxy))
    return await worker.refuel(chain_from_id, **kwargs)


async def l2pass_for_nft_attack(account_number, private_key, _, proxy, chain_from_id, **kwargs):
    network = get_network_by_chain_id(chain_from_id)

    worker = L2Pass(get_client(account_number, private_key, network, proxy))
    return await worker.bridge(chain_from_id, **kwargs)


async def l2pass_nft_attack(account_number, private_key, network, proxy):
    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.nft_attack(dapp_id=1)


async def merkly_refuel_google(account_number, private_key, _, proxy, chain_from, chain_to):
    attack_data = {
        chain_to: (0.000001, 0.0000022)
    }
    wrapped_chain_from = LAYERZERO_WRAPED_NETWORKS[chain_from]
    network = get_network_by_chain_id(wrapped_chain_from)

    worker = Merkly(get_client(account_number, private_key, network, proxy))
    return await worker.refuel(chain_from_id=wrapped_chain_from, attack_data=attack_data)


async def l2pass_refuel_google(account_number, private_key, _, proxy, chain_from, chain_to):
    attack_data = {
        chain_to: (0.000001, 0.0000022)
    }
    wrapped_chain_from = LAYERZERO_WRAPED_NETWORKS[chain_from]
    network = get_network_by_chain_id(wrapped_chain_from)

    worker = L2Pass(get_client(account_number, private_key, network, proxy))
    return await worker.refuel(chain_from_id=wrapped_chain_from, attack_data=attack_data)


async def zerius_refuel_google(account_number, private_key, _, proxy, chain_from, chain_to):
    attack_data = {
        chain_to: (0.000001, 0.0000022)
    }
    wrapped_chain_from = LAYERZERO_WRAPED_NETWORKS[chain_from]
    network = get_network_by_chain_id(wrapped_chain_from)

    worker = Zerius(get_client(account_number, private_key, network, proxy))
    return await worker.refuel(wrapped_chain_from, attack_data=attack_data)


async def l2pass_bridge_google(account_number, private_key, _, proxy, chain_from, chain_to):
    wrapped_chain_from = LAYERZERO_WRAPED_NETWORKS[chain_from]
    network = get_network_by_chain_id(wrapped_chain_from)

    worker = L2Pass(get_client(account_number, private_key, network, proxy))
    return await worker.bridge(chain_from_id=wrapped_chain_from, attack_data=chain_to)


async def zerius_bridge_google(account_number, private_key, _, proxy, chain_from, chain_to):
    wrapped_chain_from = LAYERZERO_WRAPED_NETWORKS[chain_from]
    network = get_network_by_chain_id(wrapped_chain_from)

    worker = Zerius(get_client(account_number, private_key, network, proxy))
    return await worker.bridge(wrapped_chain_from, attack_data=chain_to)


async def l2pass_refuel_attack(account_number, private_key, network, proxy):
    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.refuel_attack(dapp_id=2)


async def merkly_for_refuel_attack(account_number, private_key, _, proxy, chain_from_id, **kwargs):
    network = get_network_by_chain_id(chain_from_id)

    worker = Merkly(get_client(account_number, private_key, network, proxy))
    return await worker.refuel(chain_from_id, **kwargs)


async def merkly_refuel_attack(account_number, private_key, network, proxy):
    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.refuel_attack(dapp_id=1)


async def zerius_for_refuel_attack(account_number, private_key, _, proxy, chain_from_id, **kwargs):
    network = get_network_by_chain_id(chain_from_id)

    worker = Zerius(get_client(account_number, private_key, network, proxy))
    return await worker.refuel(chain_from_id, **kwargs)


async def zerius_refuel_attack(account_number, private_key, network, proxy):
    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.refuel_attack(dapp_id=3)


async def zerius_for_nft_attack(account_number, private_key, _, proxy, chain_from_id, **kwargs):
    network = get_network_by_chain_id(chain_from_id)

    worker = Zerius(get_client(account_number, private_key, network, proxy))
    return await worker.bridge(chain_from_id, **kwargs)


async def zerius_nft_attack(account_number, private_key, network, proxy):
    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.nft_attack(dapp_id=1)


async def refuel_zerius(account_number, private_key, _, proxy):
    chain_from_id = LAYERZERO_WRAPED_NETWORKS[random.choice(SRC_CHAIN_ZERIUS)]
    network = get_network_by_chain_id(chain_from_id)

    worker = Zerius(get_client(account_number, private_key, network, proxy))
    return await worker.refuel(chain_from_id)


async def mint_zerius(account_number, private_key, _, proxy):
    chain_from_id = LAYERZERO_WRAPED_NETWORKS[random.choice(SRC_CHAIN_ZERIUS)]
    network = get_network_by_chain_id(chain_from_id)

    worker = Zerius(get_client(account_number, private_key, network, proxy))
    return await worker.mint(chain_from_id)


async def mint_merkly(account_number, private_key, _, proxy):
    chain_from_id = LAYERZERO_WRAPED_NETWORKS[random.choice(SRC_CHAIN_MERKLY)]
    network = get_network_by_chain_id(chain_from_id)

    worker = Merkly(get_client(account_number, private_key, network, proxy))
    return await worker.mint(chain_from_id)


async def mint_l2pass(account_number, private_key, _, proxy):
    chain_from_id = LAYERZERO_WRAPED_NETWORKS[random.choice(SRC_CHAIN_L2PASS)]
    network = get_network_by_chain_id(chain_from_id)

    worker = L2Pass(get_client(account_number, private_key, network, proxy))
    return await worker.mint(chain_from_id)


async def bridge_zerius(account_number, private_key, _, proxy):
    chain_from_id = LAYERZERO_WRAPED_NETWORKS[random.choice(SRC_CHAIN_ZERIUS)]
    network = get_network_by_chain_id(chain_from_id)

    worker = Zerius(get_client(account_number, private_key, network, proxy))
    return await worker.bridge(chain_from_id)


async def bridge_l2pass(account_number, private_key, _, proxy):
    chain_from_id = LAYERZERO_WRAPED_NETWORKS[random.choice(SRC_CHAIN_L2PASS)]
    network = get_network_by_chain_id(chain_from_id)

    worker = L2Pass(get_client(account_number, private_key, network, proxy))
    return await worker.bridge(chain_from_id)


async def refuel_bungee(account_number, private_key, _, proxy):
    chain_from_id = LAYERZERO_WRAPED_NETWORKS[random.choice(SRC_CHAIN_BUNGEE)]
    network = get_network_by_chain_id(chain_from_id)

    worker = Bungee(get_client(account_number, private_key, network, proxy))
    return await worker.refuel()


async def mint_mailzero(account_number, private_key, network, proxy):
    worker = MailZero(get_client(account_number, private_key, network, proxy))
    return await worker.mint()


async def send_message_l2telegraph(account_number, private_key, _, proxy):
    chain_id_from = LAYERZERO_WRAPED_NETWORKS[random.choice(SRC_CHAIN_L2TELEGRAPH)]
    network = get_network_by_chain_id(chain_id_from)

    worker = L2Telegraph(get_client(account_number, private_key, network, proxy))
    return await worker.send_message()


async def mint_and_bridge_l2telegraph(account_number, private_key, _, proxy):
    chain_id_from = LAYERZERO_WRAPED_NETWORKS[random.choice(SRC_CHAIN_L2TELEGRAPH)]
    network = get_network_by_chain_id(chain_id_from)

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


async def okx_withdraw(account_number, private_key, network, proxy, *args, **kwargs):
    worker = OKX(get_client(account_number, private_key, network, proxy))
    return await worker.withdraw(*args, **kwargs)


async def okx_multi_withdraw(account_number, private_key, network, proxy):
    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.cex_multi_withdraw(dapp_id=1)


async def bingx_multi_withdraw(account_number, private_key, network, proxy):
    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.cex_multi_withdraw(dapp_id=2)


async def binance_multi_withdraw(account_number, private_key, network, proxy):
    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.cex_multi_withdraw(dapp_id=3)


async def random_okx_withdraw(account_number, private_key, network, proxy):
    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.random_cex_withdraw(dapp_id=1)


async def random_bingx_withdraw(account_number, private_key, network, proxy):
    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.random_cex_withdraw(dapp_id=2)


async def random_binance_withdraw(account_number, private_key, network, proxy):
    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.random_cex_withdraw(dapp_id=3)


async def okx_deposit(account_number, private_key, _, proxy, dep_network=OKX_DEPOSIT_NETWORK, **kwargs):
    network = get_network_by_chain_id(CEX_WRAPED_ID[dep_network])

    worker = OKX(get_client(account_number, private_key, network, proxy))
    return await worker.deposit(**kwargs)


async def bingx_deposit(account_number, private_key, _, proxy, dep_network=BINGX_DEPOSIT_NETWORK, **kwargs):
    network = get_network_by_chain_id(CEX_WRAPED_ID[dep_network])

    worker = BingX(get_client(account_number, private_key, network, proxy))
    return await worker.deposit(**kwargs)


async def binance_deposit(account_number, private_key, _, proxy, dep_network=BINANCE_DEPOSIT_NETWORK, **kwargs):
    network = get_network_by_chain_id(CEX_WRAPED_ID[dep_network])

    worker = Binance(get_client(account_number, private_key, network, proxy))
    return await worker.deposit(**kwargs)


async def okx_limiter_deposit(account_number, private_key, _, proxy):
    network = get_network_by_chain_id(CEX_WRAPED_ID[OKX_DEPOSIT_NETWORK])

    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.cex_limiter_deposit(dapp_id=1)


async def bingx_limiter_deposit(account_number, private_key, _, proxy):
    network = get_network_by_chain_id(CEX_WRAPED_ID[BINGX_DEPOSIT_NETWORK])

    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.cex_limiter_deposit(dapp_id=2)


async def binance_limiter_deposit(account_number, private_key, _, proxy):
    network = get_network_by_chain_id(CEX_WRAPED_ID[BINANCE_DEPOSIT_NETWORK])

    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.cex_limiter_deposit(dapp_id=3)


async def smart_cex_deposit(account_number, private_key, network, proxy):
    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.smart_cex_deposit(dapp_id=1)


async def swap_jediswap(account_number, private_key, network, proxy, *args, **kwargs):
    worker = JediSwap(get_client(account_number, private_key, network, proxy))
    return await worker.swap(*args, **kwargs)


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
    blockchain = get_interface_by_chain_id(GLOBAL_NETWORK)

    worker = blockchain(get_client(account_number, private_key, network, proxy))
    return await worker.random_approve()


async def smart_random_approve(account_number, private_key, network, proxy):

    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.smart_random_approve()


async def mint_mintfun(account_number, private_key, network, proxy):

    worker = MintFun(get_client(account_number, private_key, network, proxy))
    return await worker.mint()


async def collector_eth(account_number, private_key, network, proxy):

    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.collect_eth()


async def make_balance_to_average(account_number, private_key, network, proxy):

    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.balance_average()


async def wrap_abuser(account_number, private_key, network, proxy):

    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.wraps_abuser()


async def bridge_stargate(account_number, private_key, network, proxy):
    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.smart_bridge_l0(dapp_id=1)


async def swap_stargate(client, **kwargs):
    worker = Stargate(client)
    return await worker.bridge(**kwargs)


async def bridge_coredao(account_number, private_key, network, proxy):
    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.smart_bridge_l0(dapp_id=2)


async def swap_coredao(client, **kwargs):
    worker = CoreDAO(client)
    return await worker.bridge(**kwargs)


async def swap_bridged_usdc(account_number, private_key, network, proxy):
    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.swap_bridged_usdc()


async def grapedraw_bid(account_number, private_key, network, proxy):
    worker = GrapeDraw(get_client(account_number, private_key, network, proxy))
    return await worker.bid_place()


async def smart_merkly(account_number, private_key, network, proxy):
    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.smart_refuel(dapp_id=1)


async def smart_l2pass(account_number, private_key, network, proxy):
    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.smart_refuel(dapp_id=2)


async def smart_zerius(account_number, private_key, network, proxy):
    worker = Custom(get_client(account_number, private_key, network, proxy))
    return await worker.smart_refuel(dapp_id=3)


async def bingx_withdraw(account_number, private_key, network, proxy, **kwargs):
    worker = BingX(get_client(account_number, private_key, network, proxy))
    return await worker.withdraw(**kwargs)


async def bingx_transfer(account_number, private_key, network, proxy):
    worker = BingX(get_client(account_number, private_key, network, proxy))
    return await worker.withdraw(transfer_mode=True)


async def binance_withdraw(account_number, private_key, network, proxy, **kwargs):
    worker = Binance(get_client(account_number, private_key, network, proxy))
    return await worker.withdraw(**kwargs)


async def bridge_zora(account_number, private_key, _, proxy):
    network = get_network_by_chain_id(NATIVE_CHAIN_ID_FROM)

    worker = Zora(get_client(account_number, private_key, network, proxy))
    return await worker.bridge()
