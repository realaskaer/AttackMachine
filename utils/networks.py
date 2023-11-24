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
        '',
    ],
    chain_id=0,
    eip1559_support=False,
    token='ETH',
    explorer='https://starkscan.co/',
)

zkSyncEra = Network(
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

Arbitrum = Network(
    name='Arbitrum',
    rpc=[
        'https://rpc.ankr.com/arbitrum/',
        'https://arbitrum.llamarpc.com',
        'https://1rpc.io/arb',
        'https://arb1.arbitrum.io/rpc'
    ],
    chain_id=42161,
    eip1559_support=True,
    token='ETH',
    explorer='https://arbiscan.io/',
)


Optimism = Network(
    name='Optimism',
    rpc=[
        'https://rpc.ankr.com/optimism/',
        'https://optimism.llamarpc.com',
        'https://optimism.drpc.org',
        'https://1rpc.io/op'
    ],
    chain_id=10,
    eip1559_support=True,
    token='ETH',
    explorer='https://optimistic.etherscan.io/',
)


Polygon = Network(
    name='Polygon',
    rpc=[
        'https://rpc.ankr.com/polygon',
        'https://polygon.llamarpc.com',
        'https://1rpc.io/matic',
        'https://polygon-rpc.com'
    ],
    chain_id=137,
    eip1559_support=True,
    token='MATIC',
    explorer='https://polygonscan.com/',
)


Avalanche = Network(
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


Ethereum = Network(
    name='Ethereum',
    rpc=[
        'https://rpc.ankr.com/eth',
        'https://eth.llamarpc.com',
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

Arbitrum_nova = Network(
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

Base = Network(
    name='Base',
    rpc=[
        'https://base.llamarpc.com',
        'https://base.publicnode.com',
        'https://base.meowrpc.com',
        'https://1rpc.io/base'
    ],
    chain_id=8453,
    eip1559_support=True,
    token='ETH',
    explorer='https://basescan.org/'
)

Linea = Network(
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

Zora = Network(
    name='Zora',
    rpc=[
        'https://rpc.zora.energy'
    ],
    chain_id=7777777,
    eip1559_support=False,
    token='ETH',
    explorer='https://zora.superscan.network/'
)

Polygon_ZKEVM = Network(
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

BSC = Network(
    name='BNB chain',
    rpc=[
        'https://binance.llamarpc.com',
        'https://bsc-dataseed.bnbchain.org',
        'https://rpc.ankr.com/bsc',
        'https://1rpc.io/bnb'
    ],
    chain_id=56,
    eip1559_support=False,
    token='BNB',
    explorer='https://bscscan.com/'
)

Manta = Network(
    name='Manta',
    rpc=[
        'https://pacific-rpc.manta.network/http'
    ],
    chain_id=169,
    eip1559_support=True,
    token='ETH',
    explorer='https://pacific-explorer.manta.network/'
)

Mantle = Network(
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

OpBNB = Network(
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

# zkSyncLite = Network(
#     name='zksync_lite',
#     rpc=[],
#     chain_id=0,
#     eip1559_support=True,
#     token='ETH',
#     explorer='https://zkscan.io/'
# )
