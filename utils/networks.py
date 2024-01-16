class Network:
    def __init__(
            self,
            name: str,
            rpc: list,
            chain_id: int,
            eip1559_support: bool,
            token: str,
            explorer: str,
            decimals: int = 18
    ):
        self.name = name
        self.rpc = rpc
        self.chain_id = chain_id
        self.eip1559_support = eip1559_support
        self.token = token
        self.explorer = explorer
        self.decimals = decimals

    def __repr__(self):
        return f'{self.name}'


StarknetRPC = Network(
    name='Starknet',
    rpc=[
        'https://starknet-mainnet.g.alchemy.com/v2/cUa595b4LBwHdDZ3uHSBZr7PS1NXgFCQ',
    ],
    chain_id=0,
    eip1559_support=False,
    token='ETH',
    explorer='https://starkscan.co/',
)

zkSyncEraRPC = Network(
    name='zkSync',
    rpc=[
        'https://mainnet.era.zksync.io',
    ],
    chain_id=324,
    eip1559_support=True,
    token='ETH',
    explorer='https://explorer.zksync.io/',
)

ScrollRPC = Network(
    name='Scroll',
    rpc=[
        'https://1rpc.io/scroll',
        'https://rpc.scroll.io',
        'https://scroll.blockpi.network/v1/rpc/public'
    ],
    chain_id=534352,
    eip1559_support=False,
    token='ETH',
    explorer='https://scrollscan.com/'
)

ArbitrumRPC = Network(
    name='Arbitrum',
    rpc=[
        'https://rpc.ankr.com/arbitrum/',
        'https://1rpc.io/arb',
        'https://arb1.arbitrum.io/rpc'
    ],
    chain_id=42161,
    eip1559_support=True,
    token='ETH',
    explorer='https://arbiscan.io/',
)


OptimismRPC = Network(
    name='Optimism',
    rpc=[
        'https://rpc.ankr.com/optimism/',
        'https://optimism.drpc.org',
        'https://1rpc.io/op'
    ],
    chain_id=10,
    eip1559_support=True,
    token='ETH',
    explorer='https://optimistic.etherscan.io/',
)


PolygonRPC = Network(
    name='Polygon',
    rpc=[
        'https://rpc.ankr.com/polygon',
    ],
    chain_id=137,
    eip1559_support=False,
    token='MATIC',
    explorer='https://polygonscan.com/',
)


AvalancheRPC = Network(
    name='Avalanche',
    rpc=[
        'https://rpc.ankr.com/avalanche/',
        'https://1rpc.io/avax/c',
        'https://avax.meowrpc.com',
        'https://avalanche.drpc.org'
    ],
    chain_id=43114,
    eip1559_support=True,
    token='AVAX',
    explorer='https://snowtrace.io/',
)


EthereumRPC = Network(
    name='Ethereum',
    rpc=[
        'https://rpc.ankr.com/eth',
        'https://ethereum.publicnode.com',
        'https://rpc.mevblocker.io',
        'https://rpc.flashbots.net',
        'https://1rpc.io/eth',
        'https://eth.drpc.org'
    ],
    chain_id=1,
    eip1559_support=True,
    token='ETH',
    explorer='https://etherscan.io/'
)

Arbitrum_novaRPC = Network(
    name='Arbitrum Nova',
    rpc=[
        'https://rpc.ankr.com/arbitrumnova',
        'https://arbitrum-nova.publicnode.com',
        'https://arbitrum-nova.drpc.org',
        'https://nova.arbitrum.io/rpc'
    ],
    chain_id=42170,
    eip1559_support=True,
    token='ETH',
    explorer='https://nova.arbiscan.io/'
)

BaseRPC = Network(
    name='Base',
    rpc=[
        'https://mainnet.base.org',
    ],
    chain_id=8453,
    eip1559_support=True,
    token='ETH',
    explorer='https://basescan.org/'
)

LineaRPC = Network(
    name='Linea',
    rpc=[
        'https://linea.drpc.org',
        'https://1rpc.io/linea',
        'https://rpc.linea.build'
    ],
    chain_id=59144,
    eip1559_support=False,
    token='ETH',
    explorer='https://lineascan.build/'
)

ZoraRPC = Network(
    name='Zora',
    rpc=[
        'https://rpc.zora.energy'
    ],
    chain_id=7777777,
    eip1559_support=False,
    token='ETH',
    explorer='https://zora.superscan.network/'
)

Polygon_ZKEVM_RPC = Network(
    name='Polygon ZKEVM',
    rpc=[
        'https://1rpc.io/polygon/zkevm',
        'https://zkevm-rpc.com',
        'https://rpc.ankr.com/polygon_zkevm'
    ],
    chain_id=1101,
    eip1559_support=True,
    token='ETH',
    explorer='https://zkevm.polygonscan.com/'
)

BSC_RPC = Network(
    name='BNB Chain',
    rpc=[
        'https://rpc.ankr.com/bsc',
    ],
    chain_id=56,
    eip1559_support=False,
    token='BNB',
    explorer='https://bscscan.com/'
)

MantaRPC = Network(
    name='Manta',
    rpc=[
        'https://pacific-rpc.manta.network/http'
    ],
    chain_id=169,
    eip1559_support=True,
    token='ETH',
    explorer='https://pacific-explorer.manta.network/'
)

MantleRPC = Network(
    name='Mantle',
    rpc=[
        'https://mantle.publicnode.com',
        'https://mantle-mainnet.public.blastapi.io',
        'https://mantle.drpc.org',
        'https://rpc.ankr.com/mantle',
        'https://1rpc.io/mantle'
    ],
    chain_id=5000,
    eip1559_support=True,
    token='MNT',
    explorer='https://explorer.mantle.xyz/'
)

OpBNB_RPC = Network(
    name='OpBNB',
    rpc=[
        'https://opbnb.publicnode.com',
        'https://1rpc.io/opbnb',
        'https://opbnb-mainnet-rpc.bnbchain.org',
        'https://opbnb-mainnet.nodereal.io/v1/e9a36765eb8a40b9bd12e680a1fd2bc5',
    ],
    chain_id=204,
    eip1559_support=False,
    token='BNB',
    explorer='https://opbnbscan.com/'
)

MoonbeamRPC = Network(
    name='Moonbeam',
    rpc=[
        'https://moonbeam.public.blastapi.io',
    ],
    chain_id=1284,
    eip1559_support=False,
    token='GLMR',
    explorer='https://moonscan.io/'
)

MoonriverRPC = Network(
    name='Moonriver',
    rpc=[
        'https://moonriver.public.blastapi.io',
    ],
    chain_id=1285,
    eip1559_support=False,
    token='MOVR',
    explorer='https://moonriver.moonscan.io/'
)


HarmonyRPC = Network(
    name='Harmony One',
    rpc=[
        'https://api.harmony.one',
        'https://api.s0.t.hmny.io',
        'https://a.api.s0.t.hmny.io',
        'https://endpoints.omniatech.io/v1/harmony/mainnet-0/public',
        'https://1rpc.io/one',
    ],
    chain_id=1666600000,
    eip1559_support=False,
    token='ONE',
    explorer='https://explorer.harmony.one/'
)

TelosRPC = Network(
    name='Telos',
    rpc=[
        'https://mainnet.telos.net/evm',
        'https://rpc1.eu.telos.net/evm',
        'https://rpc1.us.telos.net/evm',
        'https://api.kainosbp.com/evm',
    ],
    chain_id=40,
    eip1559_support=False,
    token='TLOS',
    explorer='https://explorer.telos.net/'
)

CeloRPC = Network(
    name='Celo',
    rpc=[
        'https://forno.celo.org',
        'https://rpc.ankr.com/celo',
        'https://1rpc.io/celo',
    ],
    chain_id=42220,
    eip1559_support=False,
    token='CELO',
    explorer='https://explorer.celo.org/mainnet/'
)

GnosisRPC = Network(
    name='Gnosis',
    rpc=[
        'https://gnosis.drpc.org',
        'https://1rpc.io/gnosis',
    ],
    chain_id=100,
    eip1559_support=False,
    token='XDAI',
    explorer='https://gnosisscan.io/'
)

CoreRPC = Network(
    name='CoreDAO',
    rpc=[
        'https://core.public.infstones.com',
        'https://rpc.ankr.com/core',
        'https://1rpc.io/core',
        'https://rpc.coredao.org',
    ],
    chain_id=1116,
    eip1559_support=False,
    token='CORE',
    explorer='https://scan.coredao.org/'
)

TomoChainRPC = Network(
    name='TomoChain',
    rpc=[
        'https://rpc.tomochain.com',
        'https://tomo.blockpi.network/v1/rpc/public',
        'https://viction.blockpi.network/v1/rpc/public',
    ],
    chain_id=88,
    eip1559_support=False,
    token='TOMO',
    explorer='https://tomoscan.io/'
)

ConfluxRPC = Network(
    name='Conflux',
    rpc=[
        'https://evm.confluxrpc.com',
    ],
    chain_id=1030,
    eip1559_support=False,
    token='CFX',
    explorer='https://www.confluxscan.net/'
)

OrderlyRPC = Network(
    name='Orderly',
    rpc=[
        'https://l2-orderly-mainnet-0.t.conduit.xyz',
        'https://rpc.orderly.network',
    ],
    chain_id=291,
    eip1559_support=False,
    token='ETH',
    explorer='https://explorer.orderly.network/'
)

HorizenRPC = Network(
    name='Horizen EON',
    rpc=[
        'https://rpc.ankr.com/horizen_eon',
        'https://eon-rpc.horizenlabs.io/ethv1',
    ],
    chain_id=7332,
    eip1559_support=False,
    token='ZEN',
    explorer='https://opbnbscan.com/'
)

MetisRPC = Network(
    name='Metis',
    rpc=[
        'https://metis-mainnet.public.blastapi.io',
        'https://metis-pokt.nodies.app',
        'https://andromeda.metis.io/?owner=1088'
    ],
    chain_id=1088,
    eip1559_support=False,
    token='METIS',
    explorer='https://explorer.metis.io/'
)

AstarRPC = Network(
    name='Astar',
    rpc=[
        'https://evm.astar.network',
        'https://astar.public.blastapi.io',
        'https://1rpc.io/astr',
        'https://astar-rpc.dwellir.com'
    ],
    chain_id=592,
    eip1559_support=False,
    token='ASTR',
    explorer='https://explorer.metis.io/'
)

KavaRPC = Network(
    name='Kava',
    rpc=[
        'https://kava-evm.publicnode.com',
        'https://kava-pokt.nodies.app',
        'https://evm.kava.io',
    ],
    chain_id=2222,
    eip1559_support=False,
    token='KAVA',
    explorer='https://kavascan.com/'
)

KlaytnRPC = Network(
    name='Klaytn',
    rpc=[
        'https://rpc.ankr.com/klaytn',
        'https://klaytn.blockpi.network/v1/rpc/public',
        'https://1rpc.io/klay',
        'https://klaytn-pokt.nodies.app'
    ],
    chain_id=8217,
    eip1559_support=False,
    token='KLAY',
    explorer='https://klaytnscope.com/'
)

FantomRPC = Network(
    name='Fantom',
    rpc=[
        'https://rpcapi.fantom.network',
        'https://endpoints.omniatech.io/v1/fantom/mainnet/public',
        'https://rpc.ankr.com/fantom',
    ],
    chain_id=250,
    eip1559_support=False,
    token='FTM',
    explorer='https://ftmscan.com/'
)

AuroraRPC = Network(
    name='Aurora',
    rpc=[
        'https://mainnet.aurora.dev',
        'https://endpoints.omniatech.io/v1/aurora/mainnet/public',
        'https://1rpc.io/aurora',
        'https://aurora.drpc.org'
    ],
    chain_id=1313161554,
    eip1559_support=False,
    token='ETH',
    explorer='https://explorer.aurora.dev/'
)

CantoRPC = Network(
    name='Canto',
    rpc=[
        'https://canto.gravitychain.io',
        'https://jsonrpc.canto.nodestake.top',
        'https://mainnode.plexnode.org:8545',
        'https://canto.slingshot.finance'
    ],
    chain_id=7700,
    eip1559_support=False,
    token='CANTO',
    explorer='https://cantoscan.com/'
)

DFK_RPC = Network(
    name='DFK',
    rpc=[
        'https://avax-pokt.nodies.app/ext/bc/q2aTwKuyzgs8pynF7UXBZCU7DejbZbZ6EUyHr3JQzYgwNPUPi/rpc',
        'https://dfkchain.api.onfinality.io/public',
        'https://mainnode.plexnode.org:8545',
        'https://subnets.avax.network/defi-kingdoms/dfk-chain/rpc'
    ],
    chain_id=53935,
    eip1559_support=False,
    token='JEWEL',
    explorer='https://avascan.info/blockchain/dfk'
)

FuseRPC = Network(
    name='Fuse',
    rpc=[
        'https://rpc.fuse.io',
        'https://fuse-pokt.nodies.app',
        'https://fuse.liquify.com',
        'https://fuse.api.onfinality.io/public'
    ],
    chain_id=122,
    eip1559_support=False,
    token='FUSE',
    explorer='https://cantoscan.com/'
)

GoerliRPC = Network(
    name='Goerli',
    rpc=[
        'https://endpoints.omniatech.io/v1/eth/goerli/public',
        'https://rpc.ankr.com/eth_goerli',
        'https://eth-goerli.public.blastapi.io',
        'https://goerli.blockpi.network/v1/rpc/public'
    ],
    chain_id=5,
    eip1559_support=False,
    token='ETH',
    explorer='https://goerli.etherscan.io/'
)

MeterRPC = Network(
    name='Meter',
    rpc=[
        'https://rpc.meter.io',
        'https://rpc-meter.jellypool.xyz',
        'https://meter.blockpi.network/v1/rpc/public',
    ],
    chain_id=82,
    eip1559_support=False,
    token='MTR',
    explorer='https://scan.meter.io/'
)

OKX_RPC = Network(
    name='OKX Chain',
    rpc=[
        'https://exchainrpc.okex.org',
        'https://oktc-mainnet.public.blastapi.io',
        'https://1rpc.io/oktc',
        'https://okt-chain.api.onfinality.io/public'
    ],
    chain_id=66,
    eip1559_support=False,
    token='OKT',
    explorer='https://www.oklink.com/ru/oktc'
)

ShimmerRPC = Network(
    name='Shimmer',
    rpc=[
        'https://json-rpc.evm.shimmer.network',
    ],
    chain_id=148,
    eip1559_support=False,
    token='SMR',
    explorer='https://explorer.shimmer.network/'
)

TenetRPC = Network(
    name='Tenet',
    rpc=[
        'https://rpc.tenet.org',
        'https://tenet-evm.publicnode.com',
    ],
    chain_id=1559,
    eip1559_support=False,
    token='TENET',
    explorer='https://tenetscan.io/'
)

XPLA_RPC = Network(
    name='XPLA',
    rpc=[
        'https://dimension-evm-rpc.xpla.dev	',
    ],
    chain_id=37,
    eip1559_support=False,
    token='XPLA',
    explorer='https://explorer.xpla.io/'
)

LootChainRPC = Network(
    name='LootChain',
    rpc=[
        'https://rpc.lootchain.com/http',
    ],
    chain_id=5151706,
    eip1559_support=False,
    token='AGLD',
    explorer='https://explorer.lootchain.com/'
)

ZKFairRPC = Network(
    name='ZKFair',
    rpc=[
        'https://rpc.zkfair.io',
        'https://zkfair.rpc.thirdweb.com',
    ],
    chain_id=42766,
    eip1559_support=False,
    token='USDC',
    explorer='https://scan.zkfair.io/'
)

BeamRPC = Network(
    name='Beam',
    rpc=[
        'https://subnets.avax.network/beam/mainnet/rpc'
    ],
    chain_id=4337,
    eip1559_support=False,
    token='Beam',
    explorer='https://4337.snowtrace.io/'
)

# zkSyncLite = Network(
#     name='zksync_lite',
#     rpc=[],
#     chain_id=0,
#     eip1559_support=True,
#     token='ETH',
#     explorer='https://zkscan.io/'
# )
