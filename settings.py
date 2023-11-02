"""
-------------------------------------------------OKX WITHDRAW-----------------------------------------------------------
    Choose withdrawal network. The software works only with ETH withdraw
    Don't forget to insert your API_KEYs
    
    1 - ETH-ERC20
    2 - ETH-Arbitrum One
    3 - ETH-zkSync Lite | only for withdraw from OKX
    4 - ETH-Optimism
    5 - ETH-Starknet | only for withdraw from OKX
    6 - ETH-zkSync Era
    7 - ETH-Linea
    
    OKX_NETWORK_ID = 2 
    OKX_AMOUNT_MIN = 0.009  ( ETH )
    OKX_AMOUNT_MAX = 0.012  ( ETH )
------------------------------------------------------------------------------------------------------------------------
"""
OKX_NETWORK_ID = 2
OKX_AMOUNT_MIN = 0.002  # ETH
OKX_AMOUNT_MAX = 0.002  # ETH
OKX_WITHDRAW_NETWORK = 6
"""
--------------------------------------------------txSync BRIDGE---------------------------------------------------------
    Ex official bridge from zkSync. Specify the minimum and maximum of deposit/withdraw in ETH
    
    TXSYNC_DEP_MIN = 0.01 ( ETH )
    TXSYNC_DEP_MAX = 0.02 ( ETH )
    TXSYNC_WITHDRAW_MIN = 0.02 ( ETH )
    TXSYNC_WITHDRAW_MAX = 0.02 ( ETH )
"""
TXSYNC_DEP_MIN = 0.01  # ETH
TXSYNC_DEP_MAX = 0.02  # ETH
TXSYNC_WITHDRAW_MIN = 0.001  # ETH
TXSYNC_WITHDRAW_MAX = 0.002  # ETH

"""
------------------------------------------------LayerSwap BRIDGE--------------------------------------------------------
    Check available tokens and networks for bridge before setting values
    Don't forget to insert your API_KEY
       
    Arbitrum Nova = 1       Mantle = 9
    Arbitrum = 2            opBNB = 10
    Avax = 3                Optimism = 11
    Base = 4                Polygon ZKEVM = 12
    BSC = 5                 Polygon = 13
    Ethereum = 6            Scroll = 14
    Linea = 7               zkSync Era = 15
    Manta = 8               zkSync Lite = 16 # ONLY DEPOSIT (CHAIN_ID_TO)
                            Zora = 17

    LAYERSWAP_REFUEL means to add a little amount of native tokens to destination chain
    LAYERSWAP_CHAIN_ID_FROM(TO) = [2, 4, 17] One network in list will be chosen
"""
LAYERSWAP_CHAIN_ID_FROM = [2]  # BRIDGE FROM
LAYERSWAP_CHAIN_ID_TO = [15]  # BRIDGE TO
LAYERSWAP_TOKEN_FROM = 'ETH'
LAYERSWAP_TOKEN_TO = 'ETH'
LAYERSWAP_AMOUNT_MIN = 0.002  # LAYERSWAP_TOKEN_FROM
LAYERSWAP_AMOUNT_MAX = 0.0025  # LAYERSWAP_TOKEN_FROM
LAYERSWAP_REFUEL = False  # True or False

"""
------------------------------------------------ORBITER BRIDGE----------------------------------------------------------
    Check available tokens and networks for bridge before setting values 

    Arbitrum = 1            OpBNB = 9
    Arbitrum Nova = 2       Optimism = 10
    BNB Chain = 3           Polygon = 11
    Base = 4                Polygon zkEVM = 12
    Ethereum = 5            Scroll = 13
    Linea = 6               Zora = 14
    Mantle = 7              zkSync Era = 15
    Manta = 8               zkSync Lite = 16 # ONLY DEPOSIT (CHAIN_ID_TO)

    ORBITER_CHAIN_ID_FROM(TO) = [2, 4, 15] One network in list will be chosen
    ORBITER_TOKEN_NAME = 'ETH' | Orbiter support exchange only similar coins
"""
ORBITER_CHAIN_ID_FROM = [1]  # BRIDGE FROM
ORBITER_CHAIN_ID_TO = [15]  # BRIDGE TO
ORBITER_TOKEN_NAME = 'ETH'
ORBITER_AMOUNT_MIN = 0.009  # ORBITER_TOKEN_FROM
ORBITER_AMOUNT_MAX = 0.012  # ORBITER_TOKEN_FROM


"""
----------------------------------------------AMOUNT CONTROL------------------------------------------------------------
    Exchange of all tokens(include LP tokens), except ETH, is 100% of the balance 
    You specify how much ETH in % will be exchanged for the tokens.
    OKX_DEPOSIT USE THIS AMOUNT.
    
    MIN_BALANCE set the amount of ETH on the account balance, enabling the software working.
    
    AMOUNT_MIN = 70 ( % ) of token balance 
    AMOUNT_MAX = 80 ( % ) of token balance 
    MIN_BALANCE = 0.001 ( ETH ) 
"""
AMOUNT_MIN = 70  # %
AMOUNT_MAX = 80  # %
MIN_BALANCE = 0.001  # ETH

"""
--------------------------------------------ADD LIQUIDITY TO DEX--------------------------------------------------------
    DEX include Mute, SyncSwap, Maverick
    Liquidity is added only to interact with the new contract
    
    DEX_LP_MIN = 0.0005 ( ETH ) 
    DEX_LP_MAX = 0.0015 ( ETH )
    WITHDRAW_LP = Fasle # Perform withdrawal after deposit or not?
"""
DEX_LP_MIN = 0.0005  # ETH
DEX_LP_MAX = 0.001  # ETH
WITHDRAW_LP = False  # True or False

"""
---------------------------------------------LayerZero CONTROL----------------------------------------------------------
    Check website for working destination networks and min/max amount before setting values
    One network in list will be chosen
    
   *Arbitrum = 1         Kava = 15
    Astar = 2            Klaytn = 16
   *Aurora = 3           Linea = 17
   *Avalanche = 4        Meter = 18
   *Base = 5             Metis = 19
   *BNB chain = 6        Moonbeam = 20
    Canto = 7            Moonriver = 21
    Celo = 8             Nova = 22
    Core = 9             OpBNB = 23
    Ethereum = 10       *Optimism = 24
    Fantom = 11         *Polygon = 25
    Fuse = 12           *Polygon ZKEVM = 26
   *Gnosis = 13          Scroll = 27
    Harmony = 14         Tenet = 28
                         zkSync Era = 29
    
        
    DESTINATION_MERKLY_AMOUNT = {
        1: (0.0016, 0.002), # Chain ID: (min amount, max amount) in destination native**
        2: (0.0002, 0.0005) # Chain ID: (min amount, max amount) in destination native**
    }
    
    DESTINATION_L2TELEGRAPH = [22, 24, 4] 
    
    * - Supported networks in Bungee
    ** - Amount for merkly needs to be given in the native token of destination network. And also decrease the maximum
         amount by 5-10% to avoid errors. You can see maximum amount to refuel on https://minter.merkly.com/gas  
"""
DESTINATION_MERKLY_DATA = {
    2: (0.03, 0.05),  # Chain ID: (min amount , max amount) in destination native
    28: (0.04, 0.05)  # Chain ID: (min amount, max amount) in destination native
}

DESTINATION_BUNGEE_DATA = {
    3:  (0.001, 0.0015),  # Chain ID: (min amount, max amount) in ETH
    13: (0.001, 0.0015)  # Chain ID: (min amount, max amount) in ETH
}

DESTINATION_L2TELEGRAPH = [22, 24, 4]  # [Chain ID, Chain ID, Chain ID]

"""
------------------------------------------------TRANSFERS CONTROL-------------------------------------------------------
    Specify min/max amount to send to other users wallets in ETH 
    
    TRANSFER_MIN = 0.00001 ( ETH ) 
    TRANSFER_MAX = 0.00005 ( ETH )
"""
TRANSFER_MIN = 0.00001  # ETH
TRANSFER_MAX = 0.00005  # ETH

"""
------------------------------------------------GENERAL SETTINGS--------------------------------------------------------


    TX_COUNT = [70, 80] | [min, max] number of transactions needed

    MAX_UNQ_CONTACT = False | enable/disable maximum number of unique contracts.
    (The software will run each module at least once, if the number of needed transactions allows it)

    SOFTWARE_MODE = 0 | this setting is used to set the mode of the software.
    1 - Mode without deposit to OKX. A group of wallets works at the same time.
    0 - Mode with deposit on OKX. Only 1 account work at the same time.

    GAS_MULTIPLIER = 1.1 | multiply gas limit by this value
    UNLIMITED_APPROVE = False | unlimited approve for spender contract (2**256-1 of needed tokens)
"""
SOFTWARE_MODE = 0  # 0 / 1
TX_COUNT = [70, 80]  # [min, max] will be chosen at random between
MAX_UNQ_CONTACTS = True  # True or False

'-------------------------------------------------GAS CONTROL----------------------------------------------------------'
GAS_CONTROL = True  # True or False
MAXIMUM_GWEI = 100  # Gwei
SLEEP_TIME_GAS = 120  # Second
GAS_MULTIPLIER = 1.1  # Coefficient

'------------------------------------------------RETRY CONTROL---------------------------------------------------------'
MAXIMUM_RETRY = 1  # Times
SLEEP_TIME_RETRY = 5  # Second

'------------------------------------------------PROXY CONTROL---------------------------------------------------------'
USE_PROXY = True  # True or False

'-----------------------------------------------APPROVE CONTROL--------------------------------------------------------'
UNLIMITED_APPROVE = False  # True or False

'-----------------------------------------------SLIPPAGE CONTROL-------------------------------------------------------'
SLIPPAGE_PERCENT = 0.987  # 0.5 = 0.5%, 1 = 1%, 2 = 2%

'------------------------------------------------SLEEP CONTROL---------------------------------------------------------'
SLEEP_MODE = False  # True or False
MIN_SLEEP = 60  # Second
MAX_SLEEP = 120  # Second

'--------------------------------------------------API KEYS------------------------------------------------------------'
# OKX API KEYS https://www.okx.com/ru/account/my-api
OKX_API_KEY = ""
OKX_API_SECRET = ""
OKX_API_PASSPHRAS = ""

# INCH API KEY https://portal.1inch.dev/dashboard
ONEINCH_API_KEY = ""

# LAYERSWAP API KEY https://www.layerswap.io/dashboard
LAYERSWAP_API_KEY = ""

"""
----------------------------------------------AUTO-ROUTES CONTROL-------------------------------------------------------
    Select the required modules to interact with
    These settings will be used to generate a random auto-route if you enabled it  

    AUTO_ROUTES_MODULES_USING = {
        okx_withdraw                            : 1, | ( module name ) : ( 1 - enable, 0 - disable )
        bridge_layerswap                        : 1, | ( module name ) : ( 1 - enable, 0 - disable )
        bridge_txSync                           : 0, | ( module name ) : ( 1 - enable, 0 - disable )
        etc...
        
"""

AUTO_ROUTES_MODULES_USING = {
    'okx_withdraw'                        : 1,  # see OKX settings
    'bridge_layerswap'                    : 1,  # see LayerSwap settings
    'bridge_orbiter'                      : 0,  # see Orbiter settings
    'bridge_txsync'                       : 0,  # see txSync settings
    'add_liquidity_maverick'              : 1,  # USDC/WETH LP
    'add_liquidity_mute'                  : 1,  # USDC/WETH LP
    'add_liquidity_syncswap'              : 1,  # USDC/WETH LP
    'deposit_basilisk'                    : 1,  # including withdraw
    'deposit_eralend'                     : 1,  # including withdraw
    'deposit_reactorfusion'               : 1,  # including withdraw
    'deposit_zerolend'                    : 1,  # including withdraw
    'enable_collateral_basilisk'          : 1,  # including disable
    'enable_collateral_eralend'           : 1,  # including disable
    'enable_collateral_reactorfusion'     : 1,  # including disable
    'enable_collateral_zeroland'          : 1,  # including disable
    'swap_izumi'                          : 1,
    'swap_maverick'                       : 1,
    'swap_mute'                           : 1,
    'swap_odos'                           : 1,
    'swap_oneinch'                        : 1,
    'swap_openocean'                      : 1,
    'swap_pancake'                        : 1,
    'swap_rango'                          : 1,
    'swap_spacefi'                        : 1,
    'swap_syncswap'                       : 1,
    'swap_velocore'                       : 1,
    'swap_vesync'                         : 1,
    'swap_woofi'                          : 1,
    'swap_zkswap'                         : 1,
    'wrap_eth'                            : 1,  # including unwrap
    'create_omnisea'                      : 1,  # create new NFT collection
    'create_safe'                         : 1,  # create safe on chain
    'mint_and_bridge_l2telegraph'         : 1,  # mint and bridge nft on L2Telegraph # see LayerZero settings
    'mint_domain_ens'                     : 0,  # 0.003 ETH domain
    'mint_domain_zns'                     : 1,  # free domain
    'mint_mailzero'                       : 1,  # mint free NFT from MainZero
    'mint_tevaera'                        : 1,  # mint 2 NFT from Tevaera
    'refuel_bungee'                       : 1,  # see LayerZero settings
    'refuel_merkly'                       : 1,  # see LayerZero settings
    'send_message_dmail'                  : 1,
    'send_message_l2telegraph'            : 1,  # see LayerZero settings
    'transfer_eth'                        : 1,
    'withdraw_txsync'                     : 0,
    'okx_deposit'                         : 1
}

"""
--------------------------------------------CLASSIC-ROUTES CONTROL------------------------------------------------------
    Select the required modules to interact with
    Here you can create your own route. For each step the software will select one module from the list.
    You can set None to skip a module during the route.
    See the AUTO-ROUTES settings for list of current modules.
    
    CLASSIC_ROUTES_MODULES_USING = [
        ['okx_withdraw'],
        ['bridge_layerswap', 'bridge_txsync', None],
        ['swap_mute', 'swap_izumi', 'mint_domain_ens'],
        ...
    ]
"""
CLASSIC_ROUTES_MODULES_USING = [
    ['okx_withdraw'],
    ['bridge_layerswap'],
    ['mint_tevaera', 'mint_and_bridge_l2telegraph'],
    ['enable_collateral_basilisk', 'enable_collateral_eralend', None],
    ['swap_rango', 'swap_zkswap'],
    ['refuel_merkly', 'swap_syncswap'],
    ['mint_domain_zns', 'mint_domain_ens'],
    ['wrap_eth', 'swap_pancake'],
    ['swap_mute', 'swap_spacefi', 'swap_pancake'],
    ['refuel_bungee', 'refuel_merkly'],
    ['swap_oneinch', 'mint_domain_ens'],
    ['mint_mailzero', 'swap_vesync'],
    ['withdraw_txsync']
]


