import random

from modules import *
from utils.networks import *
from config import OMNICHAIN_WRAPED_NETWORKS
from general_settings import GLOBAL_NETWORK
from settings import (SRC_CHAIN_MERKLY, SRC_CHAIN_ZERIUS, SRC_CHAIN_L2PASS, SRC_CHAIN_BUNGEE,
                      SRC_CHAIN_L2TELEGRAPH, NATIVE_CHAIN_ID_FROM, L2PASS_GAS_STATION_ID_FROM, SRC_CHAIN_WHALE,
                      CUSTOM_SWAP_DATA, SRC_CHAIN_NOGEM, NOGEM_FILLER_ID_FROM)


def get_client(account_name, private_key, network, proxy) -> Client:
    return Client(account_name, private_key, network, proxy)


def get_interface_by_chain_id(chain_id):
    return {
        2: ArbitrumNova,
        3: Base,
        4: Linea,
        8: Scroll,
        10: PolygonZkEVM,
        11: ZkSync,
        12: Zora,
        13: Ethereum,
        49: Blast
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
        # 9: StarknetRPC,
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
        48: RaribleRPC,
        49: BlastRPC,
        50: ModeRPC,
    }[chain_id]


async def cex_deposit_util(current_client, dapp_id:int, deposit_data:tuple):
    class_name = {
        1: OKX,
        2: BingX,
        3: Binance,
        4: Bitget
    }[dapp_id]

    return await class_name(current_client).deposit(deposit_data=deposit_data)


async def okx_deposit(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_cex_deposit(dapp_id=1)


async def bingx_deposit(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_cex_deposit(dapp_id=2)


async def binance_deposit(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_cex_deposit(dapp_id=3)


async def bitget_deposit(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_cex_deposit(dapp_id=4)


async def bridge_utils(current_client, dapp_id, chain_from_id, bridge_data, need_fee=False):

    class_bridge = {
        1: Across,
        2: Bungee,
        3: LayerSwap,
        4: Nitro,
        5: Orbiter,
        6: Owlto,
        7: Relay,
        8: Rhino,
        9: NativeBridge,
    }[dapp_id]

    return await class_bridge(current_client).bridge(chain_from_id, bridge_data, need_check=need_fee)


async def bridge_across(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_bridge(dapp_id=1)


async def bridge_bungee(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_bridge(dapp_id=2)


async def bridge_layerswap(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_bridge(dapp_id=3)


async def bridge_nitro(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_bridge(dapp_id=4)


async def bridge_orbiter(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_bridge(dapp_id=5)


async def bridge_owlto(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_bridge(dapp_id=6)


async def bridge_relay(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_bridge(dapp_id=7)


async def bridge_rhino(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_bridge(dapp_id=8)


async def bridge_native(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_bridge(dapp_id=9)


async def omnichain_util(
        account_name, private_key, proxy, chain_from_id:int = 0, chain_to:int = 0, dapp_id:int = 0,
        dapp_mode:int | str = 0, google_mode:bool = False, attack_data:dict | int = None,
        need_check:bool = False,
):

    class_name, src_chain = {
        1: (L2Pass, SRC_CHAIN_L2PASS),
        2: (Nogem, SRC_CHAIN_NOGEM),
        3: (Merkly, SRC_CHAIN_MERKLY),
        4: (Whale, SRC_CHAIN_WHALE),
        5: (Zerius, SRC_CHAIN_ZERIUS),
    }[dapp_id]

    if google_mode:
        attack_data = {
            chain_to: (0.000001, 0.0000045)
        } if dapp_mode == 1 else chain_to

    source_chain_id = random.choice(src_chain) if not chain_from_id else chain_from_id
    wrapped_chain_id = OMNICHAIN_WRAPED_NETWORKS[source_chain_id]
    network = get_network_by_chain_id(wrapped_chain_id)
    worker = class_name(get_client(account_name, private_key, network, proxy))

    if dapp_mode in [1, 2]:
        func = {
            1: worker.refuel,
            2: worker.bridge,
        }[dapp_mode]
    else:
        func = {
            'bridge NFT Hyperlane': worker.hnft_bridge,
            'bridge Token Hyperlane': worker.ht_bridge,
        }[dapp_mode]

    return await func(wrapped_chain_id, attack_data=attack_data, google_mode=google_mode, need_check=need_check)


async def bridge_l2pass(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_layerzero_util(dapp_id=1, dapp_mode=2)


async def bridge_nogem(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_layerzero_util(dapp_id=2, dapp_mode=2)


async def bridge_merkly(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_layerzero_util(dapp_id=3, dapp_mode=2)


async def bridge_whale(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_layerzero_util(dapp_id=4, dapp_mode=2)


async def bridge_zerius(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_layerzero_util(dapp_id=5, dapp_mode=2)


async def l2pass_refuel_google(account_name, private_key, _, proxy, chain_from, chain_to):
    return await omnichain_util(
        account_name, private_key, proxy, chain_from, chain_to, dapp_id=1, dapp_mode=1, google_mode=True
    )


async def nogem_refuel_google(account_name, private_key, _, proxy, chain_from, chain_to):
    return await omnichain_util(
        account_name, private_key, proxy, chain_from, chain_to, dapp_id=2, dapp_mode=1, google_mode=True
    )


async def merkly_refuel_google(account_name, private_key, _, proxy, chain_from, chain_to):
    return await omnichain_util(
        account_name, private_key, proxy, chain_from, chain_to, dapp_id=3, dapp_mode=1, google_mode=True
    )


async def whale_refuel_google(account_name, private_key, _, proxy, chain_from, chain_to):
    return await omnichain_util(
        account_name, private_key, proxy, chain_from, chain_to, dapp_id=4, dapp_mode=1, google_mode=True
    )


async def zerius_refuel_google(account_name, private_key, _, proxy, chain_from, chain_to):
    return await omnichain_util(
        account_name, private_key, proxy, chain_from, chain_to, dapp_id=5, dapp_mode=1, google_mode=True
    )


async def l2pass_bridge_google(account_name, private_key, _, proxy, chain_from, chain_to):
    return await omnichain_util(
        account_name, private_key, proxy, chain_from, chain_to, dapp_id=1, dapp_mode=2, google_mode=True
    )


async def nogem_bridge_google(account_name, private_key, _, proxy, chain_from, chain_to):
    return await omnichain_util(
        account_name, private_key, proxy, chain_from, chain_to, dapp_id=2, dapp_mode=2, google_mode=True
    )


async def merkly_bridge_google(account_name, private_key, _, proxy, chain_from, chain_to):
    return await omnichain_util(
        account_name, private_key, proxy, chain_from, chain_to, dapp_id=3, dapp_mode=2, google_mode=True
    )


async def whale_bridge_google(account_name, private_key, _, proxy, chain_from, chain_to):
    return await omnichain_util(
        account_name, private_key, proxy, chain_from, chain_to, dapp_id=4, dapp_mode=2, google_mode=True
    )


async def zerius_bridge_google(account_name, private_key, _, proxy, chain_from, chain_to):
    return await omnichain_util(
        account_name, private_key, proxy, chain_from, chain_to, dapp_id=5, dapp_mode=2, google_mode=True
    )


async def l2pass_refuel_attack(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.layerzero_attack(dapp_id=1, dapp_mode=1)


async def nogem_refuel_attack(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.layerzero_attack(dapp_id=2, dapp_mode=1)


async def merkly_refuel_attack(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.layerzero_attack(dapp_id=3, dapp_mode=1)


async def whale_refuel_attack(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.layerzero_attack(dapp_id=4, dapp_mode=1)


async def zerius_refuel_attack(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.layerzero_attack(dapp_id=5, dapp_mode=1)


async def l2pass_nft_attack(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.layerzero_attack(dapp_id=1, dapp_mode=2)


async def nogem_nft_attack(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.layerzero_attack(dapp_id=2, dapp_mode=2)


async def merkly_nft_attack(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.layerzero_attack(dapp_id=3, dapp_mode=2)


async def whale_nft_attack(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.layerzero_attack(dapp_id=4, dapp_mode=2)


async def zerius_nft_attack(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.layerzero_attack(dapp_id=5, dapp_mode=2)


async def refuel_l2pass(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_layerzero_util(dapp_id=1, dapp_mode=1)


async def refuel_nogem(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_layerzero_util(dapp_id=2, dapp_mode=1)


async def refuel_merkly(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_layerzero_util(dapp_id=3, dapp_mode=1)


async def refuel_whale(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_layerzero_util(dapp_id=4, dapp_mode=1)


async def refuel_zerius(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_layerzero_util(dapp_id=5, dapp_mode=1)


async def bridge_hyperlane_nft(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.merkly_omnichain_util(dapp_mode=3, dapp_function=2)


async def bridge_hyperlane_token(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.merkly_omnichain_util(dapp_mode=3, dapp_function=3)


async def okx_withdraw(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_cex_withdraw(dapp_id=1)


async def bingx_withdraw(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_cex_withdraw(dapp_id=2)


async def binance_withdraw(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_cex_withdraw(dapp_id=3)


async def bitget_withdraw(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_cex_withdraw(dapp_id=4)


async def swap_woofi(account_name, private_key, network, proxy, **kwargs):
    worker = WooFi(get_client(account_name, private_key, network, proxy))
    return await worker.swap(**kwargs)


async def swap_syncswap(account_name, private_key, network, proxy, **kwargs):
    worker = SyncSwap(get_client(account_name, private_key, network, proxy))
    return await worker.swap(**kwargs)


async def swap_syncswap_paymaster(account_name, private_key, network, proxy, **kwargs):
    worker = SyncSwap(get_client(account_name, private_key, network, proxy))
    return await worker.swap(paymaster_mode=True, **kwargs)


async def add_liquidity_syncswap(account_name, private_key, network, proxy):
    worker = SyncSwap(get_client(account_name, private_key, network, proxy))
    return await worker.add_liquidity()


async def add_liquidity_mute(account_name, private_key, network, proxy):
    worker = Mute(get_client(account_name, private_key, network, proxy))
    return await worker.add_liquidity()


async def add_liquidity_maverick(account_name, private_key, network, proxy):
    worker = Maverick(get_client(account_name, private_key, network, proxy))
    return await worker.add_liquidity()


async def withdraw_liquidity_maverick(account_name, private_key, network, proxy):
    worker = Maverick(get_client(account_name, private_key, network, proxy))
    return await worker.withdraw_liquidity()


async def withdraw_liquidity_mute(account_name, private_key, network, proxy):
    worker = Mute(get_client(account_name, private_key, network, proxy))
    return await worker.withdraw_liquidity()


async def withdraw_liquidity_syncswap(account_name, private_key, network, proxy):
    worker = SyncSwap(get_client(account_name, private_key, network, proxy))
    return await worker.withdraw_liquidity()


async def send_message_dmail(account_name, private_key, _, proxy):
    network = get_network_by_chain_id(GLOBAL_NETWORK)
    worker = Dmail(get_client(account_name, private_key, network, proxy))
    return await worker.send_message()


async def withdraw_native_bridge(account_name, private_key, _, proxy):
    blockchain = get_interface_by_chain_id(GLOBAL_NETWORK)
    network = get_network_by_chain_id(GLOBAL_NETWORK)

    worker = blockchain(get_client(account_name, private_key, network, proxy))
    return await worker.withdraw()


async def transfer_eth(account_name, private_key, network, proxy):
    blockchain = get_interface_by_chain_id(GLOBAL_NETWORK)

    worker = blockchain(get_client(account_name, private_key, network, proxy))
    return await worker.transfer_eth()


async def transfer_eth_to_myself(account_name, private_key, network, proxy):
    blockchain = get_interface_by_chain_id(GLOBAL_NETWORK)

    worker = blockchain(get_client(account_name, private_key, network, proxy))
    return await worker.transfer_eth_to_myself()


async def wrap_eth(account_name, private_key, network, proxy, *args):
    worker = SimpleEVM(get_client(account_name, private_key, network, proxy))
    return await worker.wrap_eth(*args)


async def unwrap_eth(account_name, private_key, network, proxy, **kwargs):
    worker = SimpleEVM(get_client(account_name, private_key, network, proxy))
    return await worker.unwrap_eth(**kwargs)


async def deploy_contract(account_name, private_key, network, proxy):
    blockchain = get_interface_by_chain_id(GLOBAL_NETWORK)

    worker = blockchain(get_client(account_name, private_key, network, proxy))
    return await worker.deploy_contract()


# async  def mint_deployed_token(account_name, private_key, network, proxy, *args, **kwargs):
#     mint = ZkSync(account_name, private_key, network, proxy)
#     await mint.mint_token()


async def swap_odos(account_name, private_key, network, proxy, **kwargs):
    worker = Odos(get_client(account_name, private_key, network, proxy))
    return await worker.swap(**kwargs)


async def swap_xyfinance(account_name, private_key, network, proxy, **kwargs):
    worker = XYfinance(get_client(account_name, private_key, network, proxy))
    return await worker.swap(**kwargs)


async def swap_rango(account_name, private_key, network, proxy, **kwargs):
    worker = Rango(get_client(account_name, private_key, network, proxy))
    return await worker.swap(**kwargs)


async def swap_openocean(account_name, private_key, network, proxy, **kwargs):
    worker = OpenOcean(get_client(account_name, private_key, network, proxy))
    return await worker.swap(**kwargs)


async def swap_oneinch(account_name, private_key, network, proxy, **kwargs):
    worker = OneInch(get_client(account_name, private_key, network, proxy))
    return await worker.swap(**kwargs)


async def swap_izumi(account_name, private_key, network, proxy, **kwargs):
    worker = Izumi(get_client(account_name, private_key, network, proxy))
    return await worker.swap(**kwargs)


async def swap_ambient(account_name, private_key, network, proxy, **kwargs):
    worker = Ambient(get_client(account_name, private_key, network, proxy))
    return await worker.swap(**kwargs)


async def swap_zebra(account_name, private_key, network, proxy):
    worker = Zebra(get_client(account_name, private_key, network, proxy))
    return await worker.swap()


async def swap_skydrome(account_name, private_key, network, proxy):
    worker = Skydrome(get_client(account_name, private_key, network, proxy))
    return await worker.swap()


async def swap_maverick(account_name, private_key, network, proxy, **kwargs):
    worker = Maverick(get_client(account_name, private_key, network, proxy))
    return await worker.swap(**kwargs)


async def swap_zkswap(account_name, private_key, network, proxy):
    worker = ZkSwap(get_client(account_name, private_key, network, proxy))
    return await worker.swap()


async def swap_spacefi(account_name, private_key, network, proxy):
    worker = SpaceFi(get_client(account_name, private_key, network, proxy))
    return await worker.swap()


async def swap_bebop(account_name, private_key, network, proxy, **kwargs):
    worker = Bebop(get_client(account_name, private_key, network, proxy))
    return await worker.swap(**kwargs)


async def one_to_many_swap_bebop(account_name, private_key, network, proxy):
    worker = Bebop(get_client(account_name, private_key, network, proxy))
    return await worker.one_to_many_swap()


async def many_to_one_swap_bebop(account_name, private_key, network, proxy, **kwargs):
    worker = Bebop(get_client(account_name, private_key, network, proxy))
    return await worker.many_to_one_swap(**kwargs)


async def full_multi_swap_bebop(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.full_multi_swap_bebop()


async def swap_thruster(account_name, private_key, network, proxy):
    worker = Thruster(get_client(account_name, private_key, network, proxy))
    return await worker.swap()


async def swap_mute(account_name, private_key, network, proxy):
    worker = Mute(get_client(account_name, private_key, network, proxy))
    return await worker.swap()


async def swap_vesync(account_name, private_key, network, proxy):
    worker = VeSync(get_client(account_name, private_key, network, proxy))
    return await worker.swap()


async def swap_pancake(account_name, private_key, network, proxy):
    worker = PancakeSwap(get_client(account_name, private_key, network, proxy))
    return await worker.swap()


async def swap_velocore(account_name, private_key, network, proxy):
    worker = Velocore(get_client(account_name, private_key, network, proxy))
    return await worker.swap()


async def deposit_eralend(account_name, private_key, network, proxy):
    worker = EraLend(get_client(account_name, private_key, network, proxy))
    return await worker.deposit()


async def withdraw_eralend(account_name, private_key, network, proxy):
    worker = EraLend(get_client(account_name, private_key, network, proxy))
    return await worker.withdraw()


async def enable_collateral_eralend(account_name, private_key, network, proxy):
    worker = EraLend(get_client(account_name, private_key, network, proxy))
    return await worker.enable_collateral()


async def disable_collateral_eralend(account_name, private_key, network, proxy):
    worker = EraLend(get_client(account_name, private_key, network, proxy))
    return await worker.disable_collateral()


async def deposit_reactorfusion(account_name, private_key, network, proxy):
    worker = ReactorFusion(get_client(account_name, private_key, network, proxy))
    return await worker.deposit()


async def withdraw_reactorfusion(account_name, private_key, network, proxy):
    worker = ReactorFusion(get_client(account_name, private_key, network, proxy))
    return await worker.withdraw()


async def enable_collateral_reactorfusion(account_name, private_key, network, proxy):
    worker = ReactorFusion(get_client(account_name, private_key, network, proxy))
    return await worker.enable_collateral()


async def disable_collateral_reactorfusion(account_name, private_key, network, proxy):
    worker = ReactorFusion(get_client(account_name, private_key, network, proxy))
    return await worker.disable_collateral()


async def deposit_basilisk(account_name, private_key, network, proxy):
    worker = Basilisk(get_client(account_name, private_key, network, proxy))
    return await worker.deposit()


async def withdraw_basilisk(account_name, private_key, network, proxy):
    worker = Basilisk(get_client(account_name, private_key, network, proxy))
    return await worker.withdraw()


async def enable_collateral_basilisk(account_name, private_key, network, proxy):
    worker = Basilisk(get_client(account_name, private_key, network, proxy))
    return await worker.enable_collateral()


async def disable_collateral_basilisk(account_name, private_key, network, proxy):
    worker = Basilisk(get_client(account_name, private_key, network, proxy))
    return await worker.disable_collateral()


async def deposit_zerolend(account_name, private_key, network, proxy):
    worker = ZeroLend(get_client(account_name, private_key, network, proxy))
    return await worker.deposit()


async def deposit_usdb_zerolend(account_name, private_key, network, proxy):
    worker = ZeroLend(get_client(account_name, private_key, network, proxy))
    return await worker.deposit_usdb()


async def withdraw_usdb_zerolend(account_name, private_key, network, proxy):
    worker = ZeroLend(get_client(account_name, private_key, network, proxy))
    return await worker.withdraw_usdb()


async def deposit_seamless(account_name, private_key, network, proxy):
    worker = Seamless(get_client(account_name, private_key, network, proxy))
    return await worker.deposit()


async def withdraw_seamless(account_name, private_key, network, proxy):
    worker = Seamless(get_client(account_name, private_key, network, proxy))
    return await worker.withdraw()


async def deposit_usdbc_seamless(account_name, private_key, network, proxy):
    worker = Seamless(get_client(account_name, private_key, network, proxy))
    return await worker.deposit_usdbc()


async def withdraw_usdbc_seamless(account_name, private_key, network, proxy):
    worker = Seamless(get_client(account_name, private_key, network, proxy))
    return await worker.withdraw_usdbc()


async def withdraw_zerolend(account_name, private_key, network, proxy):
    worker = ZeroLend(get_client(account_name, private_key, network, proxy))
    return await worker.withdraw()


async def mint_domain_zns(account_name, private_key, network, proxy):
    worker = ZkSyncNameService(get_client(account_name, private_key, network, proxy))
    return await worker.mint()


async def mint_domain_ens(account_name, private_key, network, proxy):
    worker = EraDomainService(get_client(account_name, private_key, network, proxy))
    return await worker.mint()


async def gas_station_l2pass(account_name, private_key, _, proxy):
    chain_from_id = OMNICHAIN_WRAPED_NETWORKS[random.choice(L2PASS_GAS_STATION_ID_FROM)]
    network = get_network_by_chain_id(chain_from_id)

    worker = L2Pass(get_client(account_name, private_key, network, proxy))
    return await worker.gas_station(chain_from_id)


async def filler_nogem(account_name, private_key, _, proxy):
    chain_from_id = OMNICHAIN_WRAPED_NETWORKS[random.choice(NOGEM_FILLER_ID_FROM)]
    network = get_network_by_chain_id(chain_from_id)

    worker = Nogem(get_client(account_name, private_key, network, proxy))
    return await worker.gas_station(chain_from_id)


async def refuel_bungee(account_name, private_key, _, proxy):
    chain_from_id = OMNICHAIN_WRAPED_NETWORKS[random.choice(SRC_CHAIN_BUNGEE)]
    network = get_network_by_chain_id(chain_from_id)

    worker = Bungee(get_client(account_name, private_key, network, proxy))
    return await worker.refuel()


async def mint_mailzero(account_name, private_key, network, proxy):
    worker = MailZero(get_client(account_name, private_key, network, proxy))
    return await worker.mint()


async def send_message_l2telegraph(account_name, private_key, _, proxy):
    chain_id_from = OMNICHAIN_WRAPED_NETWORKS[random.choice(SRC_CHAIN_L2TELEGRAPH)]
    network = get_network_by_chain_id(chain_id_from)

    worker = L2Telegraph(get_client(account_name, private_key, network, proxy))
    return await worker.send_message()


async def mint_and_bridge_l2telegraph(account_name, private_key, _, proxy):
    chain_id_from = OMNICHAIN_WRAPED_NETWORKS[random.choice(SRC_CHAIN_L2TELEGRAPH)]
    network = get_network_by_chain_id(chain_id_from)

    worker = L2Telegraph(get_client(account_name, private_key, network, proxy))
    return await worker.mint_and_bridge()


async def mint_tevaera(account_name, private_key, network, proxy):
    worker = Tevaera(get_client(account_name, private_key, network, proxy))
    return await worker.mint()


async def create_omnisea(account_name, private_key, network, proxy):
    worker = Omnisea(get_client(account_name, private_key, network, proxy))
    return await worker.create()


async def create_safe(account_name, private_key, network, proxy):
    worker = GnosisSafe(get_client(account_name, private_key, network, proxy))
    return await worker.create()


async def swap_uniswap(account_name, private_key, network, proxy, **kwargs):
    worker = Uniswap(get_client(account_name, private_key, network, proxy))
    return await worker.swap(**kwargs)


async def swap_bladeswap(account_name, private_key, network, proxy, **kwargs):
    worker = BladeSwap(get_client(account_name, private_key, network, proxy))
    return await worker.swap(**kwargs)


async def swap_sushiswap(account_name, private_key, network, proxy):
    worker = SushiSwap(get_client(account_name, private_key, network, proxy))
    return await worker.swap()


async def deposit_rocketsam(account_name, private_key, network, proxy):
    worker = RocketSam(get_client(account_name, private_key, network, proxy))
    return await worker.deposit()


async def withdraw_rocketsam(account_name, private_key, network, proxy):
    worker = RocketSam(get_client(account_name, private_key, network, proxy))
    return await worker.withdraw()


async def deposit_layerbank(account_name, private_key, network, proxy):
    worker = LayerBank(get_client(account_name, private_key, network, proxy))
    return await worker.deposit()


async def withdraw_layerbank(account_name, private_key, network, proxy):
    worker = LayerBank(get_client(account_name, private_key, network, proxy))
    return await worker.withdraw()


async def deposit_moonwell(account_name, private_key, network, proxy):
    worker = Moonwell(get_client(account_name, private_key, network, proxy))
    return await worker.deposit()


async def withdraw_moonwell(account_name, private_key, network, proxy):
    worker = Moonwell(get_client(account_name, private_key, network, proxy))
    return await worker.withdraw()


async def enable_collateral_layerbank(account_name, private_key, network, proxy):
    worker = LayerBank(get_client(account_name, private_key, network, proxy))
    return await worker.enable_collateral()


async def disable_collateral_layerbank(account_name, private_key, network, proxy):
    worker = LayerBank(get_client(account_name, private_key, network, proxy))
    return await worker.disable_collateral()


async def enable_collateral_moonwell(account_name, private_key, network, proxy):
    worker = Moonwell(get_client(account_name, private_key, network, proxy))
    return await worker.enable_collateral()


async def disable_collateral_moonwell(account_name, private_key, network, proxy):
    worker = Moonwell(get_client(account_name, private_key, network, proxy))
    return await worker.disable_collateral()


async def enable_collateral_seamless(account_name, private_key, network, proxy):
    worker = Seamless(get_client(account_name, private_key, network, proxy))
    return await worker.enable_collateral()


async def disable_collateral_seamless(account_name, private_key, network, proxy):
    worker = Seamless(get_client(account_name, private_key, network, proxy))
    return await worker.disable_collateral()


async def mint_zkstars(account_name, private_key, network, proxy):
    worker = ZkStars(get_client(account_name, private_key, network, proxy))
    return await worker.mint()


async def random_approve(account_nameaccount_name, private_key, network, proxy):
    blockchain = get_interface_by_chain_id(GLOBAL_NETWORK)

    worker = blockchain(get_client(account_nameaccount_name, private_key, network, proxy))
    return await worker.random_approve()


async def smart_random_approve(account_name, private_key, network, proxy):

    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_random_approve()


async def mint_mintfun(account_name, private_key, network, proxy):

    worker = MintFun(get_client(account_name, private_key, network, proxy))
    return await worker.mint()


async def mint_hypercomic(account_name, private_key, network, proxy):

    worker = HyperComic(get_client(account_name, private_key, network, proxy))
    return await worker.mint()


async def collector_eth(account_name, private_key, network, proxy):

    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.collect_eth()


async def make_balance_to_average(account_name, private_key, network, proxy):

    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.balance_average()


async def wrap_abuser(account_name, private_key, network, proxy):

    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.wraps_abuser()


async def bridge_stargate_dust(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_bridge_l0(dapp_id=1, dust_mode=True)


async def bridge_stargate(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_bridge_l0(dapp_id=1)


async def bridge_coredao(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_bridge_l0(dapp_id=2)


async def swap_bridged_usdc(account_name, private_key, _, proxy):
    network = PolygonRPC
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.swap_bridged_usdc()


async def grapedraw_bid(account_name, private_key, network, proxy):
    worker = GrapeDraw(get_client(account_name, private_key, network, proxy))
    return await worker.bid_place()


async def okx_withdraw_util(current_client, **kwargs):
    worker = OKX(current_client)
    return await worker.withdraw(**kwargs)


async def bingx_withdraw_util(current_client, **kwargs):
    worker = BingX(current_client)
    return await worker.withdraw(**kwargs)


async def binance_withdraw_util(current_client, **kwargs):
    worker = Binance(current_client)
    return await worker.withdraw(**kwargs)


async def bitget_withdraw_util(current_client, **kwargs):
    worker = Bitget(current_client)
    return await worker.withdraw(**kwargs)


async def bingx_transfer(account_name, private_key, network, proxy):
    worker = BingX(get_client(account_name, private_key, network, proxy))
    return await worker.withdraw(transfer_mode=True)


async def bridge_zora(account_name, private_key, _, proxy):
    network = get_network_by_chain_id(random.choice(NATIVE_CHAIN_ID_FROM))

    worker = Zora(get_client(account_name, private_key, network, proxy))
    return await worker.bridge()


async def vote_rubyscore(account_name, private_key, network, proxy):
    worker = RubyScore(get_client(account_name, private_key, network, proxy))
    return await worker.vote()


async def smart_stake_stg(account_name, private_key, network, proxy):
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.smart_stake_stg()


async def check_in_owlto(account_name, private_key, network, proxy):
    worker = Owlto(get_client(account_name, private_key, network, proxy))
    return await worker.check_in()


async def custom_swap(account_name, private_key, _, proxy):
    network = get_network_by_chain_id(OMNICHAIN_WRAPED_NETWORKS[CUSTOM_SWAP_DATA[-1]])
    worker = Custom(get_client(account_name, private_key, network, proxy))
    return await worker.custom_swap()


async def claim_rewards_bungee(account_name, private_key, _, proxy):
    network = get_network_by_chain_id(1)
    worker = Bungee(get_client(account_name, private_key, network, proxy))
    return await worker.claim_rewards()


async def claim_op_across(account_name, private_key, _, proxy):
    network = get_network_by_chain_id(7)
    worker = Across(get_client(account_name, private_key, network, proxy))
    return await worker.claim_rewards()


async def rhino_recovery_funds(account_name, private_key, network, proxy):
    worker = Rhino(get_client(account_name, private_key, network, proxy))
    return await worker.recovery_funds()
