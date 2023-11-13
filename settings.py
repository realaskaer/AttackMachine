"""
-------------------------------------------------OKX WITHDRAW-----------------------------------------------------------
    Choose withdrawal | deposit network. The software works only with ETH withdraw | deposit
    Don't forget to insert your API_KEYs

   *1 - ETH-ERC20
    2 - ETH-Arbitrum One
   *3 - ETH-zkSync Lite
    4 - ETH-Optimism
   *5 - ETH-Starknet
    6 - ETH-zkSync Era
    7 - ETH-Linea

    * - software cant deposit to these chains (see OKX_DEPOSIT_NETWORK)

    OKX_WITHDRAW_NETWORK = 6
    OKX_WITHDRAW_AMOUNT  = (0.014, 0.015)  # ETH (min amount, max amount)

    OKX_BRIDGE_NEED = True | Here you can set the need for a bridge to withdraw money.
                             Maybe you already have money in the withdrawal network? (IF YES = SET FALSE)
    OKX_DEPOSIT_NETWORK = 2
    OKX_DEPOSIT_AMOUNT = 90 | % of MAX TOKEN BALANCE. Will withdraw this amount from the largest token balance in zkSync
    OKX_BRIDGE_MODE = [1, 2, 3] | 1 - Rhino.fi, 2 - Orbiter, 3 - LayerSwap. Select the bridges you need
     to transfer your funds to the network, which you choose in OKX_DEPOSIT_NETWORK. One bridge in list will be chosen.

------------------------------------------------------------------------------------------------------------------------
"""
OKX_WITHDRAW_NETWORK = 2  # NETWORK ID
OKX_WITHDRAW_AMOUNT = (0.014, 0.015)  # ETH (min amount, max amount)

OKX_BRIDGE_NEED = True  # False or True
OKX_DEPOSIT_NETWORK = 2  # NETWORK ID
OKX_DEPOSIT_AMOUNT = 90  # % of MAX TOKEN BALANCE to withdraw from zkSync Era
OKX_BRIDGE_MODE = [1]  # BRIDGES

"""
--------------------------------------------------txSync BRIDGE---------------------------------------------------------
    Ex official bridge from zkSync. Specify the minimum and maximum of deposit/withdraw in ETH
    You can specify the percentage in quotes and the software will use this setting as % of balance 

    TXSYNC_DEPOSIT_AMOUNT = (0.01, 0.02) ( ETH ) or ("10", "20") ( % )
    TXSYNC_WITHDRAW_AMOUNT = (0.01, 0.02) ( ETH ) or ("10", "20") ( % )
"""
TXSYNC_DEPOSIT_AMOUNT = (0.01, 0.02)   # ETH
TXSYNC_WITHDRAW_AMOUNT = (0.001, 0.02)  # ETH

"""
------------------------------------------------LayerSwap BRIDGE--------------------------------------------------------
    Check available tokens and networks for bridge before setting values. Works only with ETH
    You can specify the percentage in quotes and the software will use this setting as % of balance 
    Don't forget to insert your API_KEY
       
    Arbitrum = 1            Optimism = 7
    Arbitrum Nova = 2       Scroll = 8  
    Base = 3                Polygon ZKEVM = 9   
    Linea = 4               zkSync Era = 10      
    Manta = 5               Zora = 11  
    Polygon = 6             zkSync Lite = 12
    
    LAYERSWAP_CHAIN_ID_FROM(TO) = [2, 4, 16] | One network in list will be chosen
    LAYERSWAP_REFUEL | means to add a little amount of native tokens to destination chain
"""
LAYERSWAP_CHAIN_ID_FROM = [2, 10]  # BRIDGE FROM
LAYERSWAP_CHAIN_ID_TO = [11]  # BRIDGE TO
LAYERSWAP_AMOUNT = (0.018, 0.019)  # ETH or %
LAYERSWAP_REFUEL = False  # True or False

"""
------------------------------------------------ORBITER BRIDGE----------------------------------------------------------
    Check available tokens and networks for bridge before setting values. Works only with ETH
    You can specify the percentage in quotes and the software will use this setting as % of balance 

    Arbitrum = 1            Optimism = 7
    Arbitrum Nova = 2       Scroll = 8  
    Base = 3                Polygon ZKEVM = 9   
    Linea = 4               zkSync Era = 10      
    Manta = 5               Zora = 11  
    Polygon = 6             zkSync Lite = 12

    ORBITER_CHAIN_ID_FROM(TO) = [2, 4, 11] | One network in list will be chosen
"""
ORBITER_CHAIN_ID_FROM = [2, 10, 11]  # BRIDGE FROM
ORBITER_CHAIN_ID_TO = [5]  # BRIDGE TO
ORBITER_AMOUNT = (0.009, 0.012)  # ETH or %

"""
------------------------------------------------RHINO BRIDGE----------------------------------------------------------
    Check networks for bridge before setting values. Works only with ETH.
    You can specify the percentage in quotes and the software will use this setting as % of balance 
    
    Arbitrum = 1           *Polygon = 6
    Arbitrum Nova = 2       Optimism = 7
    Base = 3                Scroll = 8  
    Linea = 4               Polygon ZKEVM = 9       
    Manta = 5               zkSync Era = 10            
    
    * - Not support in RHINO_CHAIN_ID_FROM                
    RHINO_CHAIN_ID_FROM(TO) = [2, 3, 10] | One network in list will be chosen
"""
RHINO_CHAIN_ID_FROM = [8]  # BRIDGE FROM
RHINO_CHAIN_ID_TO = [1]  # BRIDGE TO
RHINO_AMOUNT = ("10", "20")  # ETH or %

"""
---------------------------------------------OMNI-CHAIN CONTROL---------------------------------------------------------
    Check website for working destination networks and min/max amount before setting values
    One network in list will be chosen

    *(B)Arbitrum = 1              Kava = 15
        Astar = 2                 Klaytn = 16
     (B)Aurora = 3               *Linea = 17
     (B)Avalanche = 4             Meter = 18
    *(B)Base = 5                  Metis = 19
        BNB chain = 6             Moonbeam = 20
        Canto = 7                 Moonriver = 21
        Celo = 8                 *Arbitrum Nova = 22
        Core = 9                  OpBNB = 23
        Ethereum = 10         *(B)Optimism = 24
        Fantom = 11           *(B)Polygon = 25
        Fuse = 12             *(B)Polygon ZKEVM = 26
        Gnosis = 13              *Scroll = 27
        Harmony = 14              Tenet = 28
                                 *zkSync Era = 29

    SOURCE_CHAIN_ZERIUS = [27, 29] | One network in list will be chosen (BRIDGE NFT)
    SOURCE_CHAIN_MERKLY = [27, 29] | One network in list will be chosen (REFUEL)
    DESTINATION_MERKLY_AMOUNT = {
        1: (0.0016, 0.002), # Chain ID: (min amount, max amount) in destination native**
        2: (0.0002, 0.0005) # Chain ID: (min amount, max amount) in destination native**
    }
    
    *   - Сan be used as a source network in ZERIUS, MERKLY
    (B)  - Supported destination networks in Bungee
    ** - Amount for merkly needs to be given in the native token of destination network. And also decrease the maximum
         amount by 5-10% to avoid errors. You can see maximum amount to refuel on https://minter.merkly.com/gas  
"""
SOURCE_CHAIN_ZERIUS = [27, 29]  # BRIDGE FROM
DESTINATION_ZERIUS = [1, 4, 8]  # BRIDGE TO

SOURCE_CHAIN_MERKLY = [1]  # REFUEL FROM
DESTINATION_MERKLY_DATA = {
    27: (0.01, 0.01),  # Chain ID: (min amount , max amount) in destination native
    28: (0.04, 0.05)  # Chain ID: (min amount, max amount) in destination native
}

DESTINATION_BUNGEE_DATA = {
    3:  (0.001, 0.0015),  # Chain ID: (min amount, max amount) in ETH
    22: (0.001, 0.0015)  # Chain ID: (min amount, max amount) in ETH
}

DESTINATION_L2TELEGRAPH = [22]  # [Chain ID, Chain ID, Chain ID]

"""
----------------------------------------------AMOUNT CONTROL------------------------------------------------------------
    Exchange of all tokens(include LP tokens), except ETH, is 100% of the balance 
    You specify how much ETH in % will be exchanged for the tokens.
    ⚠️OKX_DEPOSIT USE THIS AMOUNT.

    AMOUNT_PERCENT = (50, 60) | % of token balance for swaps(from, to) 
    LANDING_AMOUNT = (0.0005, 0.001)  | ETH or % amount for deposit on landings (from, to) 
    DEX_LP_AMOUNT = (0.0005, 0.001)  | ETH or % amount for add liquidity (from, to) 
    TRANSFER_AMOUNT = (0.00001, 0.00005)  | ETH or % amount for deposit on landings (from, to) 
    MIN_BALANCE set the amount of ETH on the account balance, enabling the software working.
"""
AMOUNT_PERCENT = (50, 60)             # % (min % , max %)
LANDING_AMOUNT = (0.0005, 0.001)      # ETH or % (from, to)
DEX_LP_AMOUNT = (0.0005, 0.001)       # ETH or % (from, to)
TRANSFER_AMOUNT = (0.00001, 0.00005)  # ETH or % (from, to)
MIN_BALANCE = 0.001  # ETH

"""
------------------------------------------------GENERAL SETTINGS--------------------------------------------------------
    GLOBAL_NETWORK = 10 | main network to interact with blockchain ⚠️
    
    Arbitrum = 1            Polygon = 6
    Arbitrum Nova = 2       Optimism = 7
    Base = 3                Scroll = 8  
    Linea = 4               Polygon ZKEVM = 9       
    Manta = 5               zkSync Era = 10       
    
    SOFTWARE_MODE = 0 | this setting is used to set the mode of the software.
    1 - Mode without deposit to OKX. A group of wallets works at the same time.
    0 - Mode with deposit on OKX. Only 1 account work at the same time.
    
    WALLETS_TO_WORK = 0 | if the value differs from zero, the software works only with the specified wallets.
    0       = all wallets will work
    3       = only wallet #3 will work
    4, 20   = wallets #4 and #20 will work
    (5, 25) = wallets from 5 to 25 will work
    
    SAVE_PROGRESS | setting enables/disables saving the progress of account progress
    TELEGRAM_NOTIFICATIONS | setting enables/disables sending messages to Telegram about account route progress
    
    GAS_MULTIPLIER = 1.1 | multiply gas limit by this value
    GAS_CONTROL = False | setting enables/disables the gas check before module startup
    UNLIMITED_APPROVE = False | unlimited approve for spender contract (2**256-1 of needed tokens)
"""
GLOBAL_NETWORK = 10  # 13.11.2023 support only zkSync. Stay tuned.
SOFTWARE_MODE = 0  # 0 / 1
WALLETS_TO_WORK = 0  # 0 / (3, 20) / 3, 20
SAVE_PROGRESS = False  # True or False
TELEGRAM_NOTIFICATIONS = False  # True or False


'-------------------------------------------------GAS CONTROL----------------------------------------------------------'
GAS_CONTROL = False  # True or False
MAXIMUM_GWEI = 100  # Gwei
SLEEP_TIME_GAS = 120  # Second
GAS_MULTIPLIER = 1.1  # Coefficient

'------------------------------------------------RETRY CONTROL---------------------------------------------------------'
MAXIMUM_RETRY = 0  # Times
SLEEP_TIME_RETRY = 5  # Second

'------------------------------------------------PROXY CONTROL---------------------------------------------------------'
USE_PROXY = False  # True or False
MOBILE_PROXY = False  # True or False
MOBILE_PROXY_URL_CHANGER = ['',
                            '',
                            '']  # ['link1', 'link2'..]

'-----------------------------------------------APPROVE CONTROL--------------------------------------------------------'
UNLIMITED_APPROVE = False  # True or False

'-----------------------------------------------SLIPPAGE CONTROL-------------------------------------------------------'
SLIPPAGE_PERCENT = 0.987  # 0.54321 = 0.54321%, 1 = 1%, 2 = 2%

'------------------------------------------------SLEEP CONTROL---------------------------------------------------------'
SLEEP_MODE = False      # True or False
SLEEP_TIME = (60, 120)  # (min seconds, max seconds)

'------------------------------------------------SECURE DATA-----------------------------------------------------------'
# OKX API KEYS https://www.okx.com/ru/account/my-api
OKX_API_KEY = ""
OKX_API_SECRET = ""
OKX_API_PASSPHRAS = ""

# EXCEL AND GOOGLE INFO
EXCEL_PASSWORD = ""
GOOGLE_SHEET_URL = ""
GOOGLE_SHEET_PAGE_NAME = ""

# TELEGRAM DATA
TG_TOKEN = ""  # https://t.me/BotFather
TG_ID = ""  # https://t.me/getmyid_bot

# INCH API KEY https://portal.1inch.dev/dashboard
ONEINCH_API_KEY = ""

# LAYERSWAP API KEY https://www.layerswap.io/dashboard
LAYERSWAP_API_KEY = ""


"""
----------------------------------------------GOOGLE-ROUTES CONTROL-----------------------------------------------------
    Technology to save account progress using Google Spreadsheets
    The software will take information from the table and based on your settings at the bottom,
     generate a route of modules for each account
     
    DMAIL_IN_ROUTES = True      | includes dmail in the transaction route
    TRANSFER_IN_ROUTES = True   | includes transfers in the transaction route
    COLLATERAL_IN_ROUTES = True | includes collateral in the transaction route
    
    DMAIL_COUNT = (1, 2)        | number of additional transactions. random (from, to)
    TRANSFER_COUNT = (1, 2)     | number of additional transactions. random (from, to)
    COLLATERAL_COUNT = (1, 2)   | number of additional transactions. random (from, to)
    
    MODULES_COUNT = (5, 10)     | number of modules to work from Google sheet. random (from, to)
    ALL_MODULES_TO_RUN = False  | all incomplete modules from the table will be added to the route
    WITHDRAW_LP = False         | when enabled, will take all liquidity out of DEX`s
    WITHDRAW_LANDING = False    | when enabled, will take all liquidity out of landing`s 
    HELP_NEW_MODULE = True      | if module completes with an error, adds a random module to the route
    EXCLUDED_MODULES = ['swap_maverick', 'create_safe'] | excludes selected modules from the route.
                                                          See classic-routes for list of modules
                                                          
    DEPOSIT_CONFIG | includes these modules in the route if necessary.
                     'okx_withdraw' will always be first in route
                     Bridges always after OKX_WITHDRAW
                     'okx_deposit' and 'okx_collect_from_sub' always last in route
    
"""

DMAIL_IN_ROUTES = True       # False or True
TRANSFER_IN_ROUTES = False    # False or True
COLLATERAL_IN_ROUTES = False  # False or True

DMAIL_COUNT = (1, 1)        # (min times , max times)
TRANSFER_COUNT = (1, 2)     # (min times , max times)
COLLATERAL_COUNT = (1, 2)   # (min times , max times)

MODULES_COUNT = (0, 0)        # (from, to)
ALL_MODULES_TO_RUN = False    # False or True
WITHDRAW_LP = False           # True or False
WITHDRAW_LANDING = False      # True or False
HELP_NEW_MODULE = False       # True or False
EXCLUDED_MODULES = ['swap_maverick', 'create_safe']

DEPOSIT_CONFIG = {
    'okx_withdraw'                        : 0,  # check OKX settings
    'bridge_rhino'                        : 0,  # check Rhino settings
    'bridge_layerswap'                    : 0,  # check LayerSwap settings
    'bridge_orbiter'                      : 0,  # check Orbiter settings
    'bridge_txsync'                       : 0,  # check txSync settings
    'okx_deposit'                         : 0,  # check OKX settings
    'okx_collect_from_sub'                : 0   # check OKX settings
}

"""
--------------------------------------------CLASSIC-ROUTES CONTROL------------------------------------------------------

    'okx_withdraw'                     # check OKX settings
    'bridge_rhino'                     # check Rhino settings
    'bridge_layerswap'                 # check LayerSwap settings
    'bridge_orbiter'                   # check Orbiter settings
    'bridge_txsync'                    # check txSync settings
    'add_liquidity_maverick'           # USDC/WETH LP
    'add_liquidity_mute'               # USDC/WETH LP
    'add_liquidity_syncswap'           # USDC/WETH LP
    'deposit_basilisk'                 
    'deposit_eralend'                  
    'deposit_reactorfusion'            
    'deposit_zerolend'                 
    'enable_collateral_basilisk'       
    'enable_collateral_eralend'        
    'enable_collateral_reactorfusion'  
    'enable_collateral_zeroland'       
    'swap_izumi'                       
    'swap_maverick'                    
    'swap_mute'                        
    'swap_odos'                        
    'swap_oneinch'                     
    'swap_openocean'                   
    'swap_pancake'                     
    'swap_rango'                       
    'swap_spacefi'                     
    'swap_syncswap'                    
    'swap_xyfinance'                   
    'swap_vesync'                      
    'swap_woofi'                       
    'swap_zkswap'                      
    'wrap_eth'                         # including unwrap
    'create_omnisea'                   # create new NFT collection
    'create_safe'                      # create safe on chain
    'mint_and_bridge_l2telegraph'      # mint and bridge nft on L2Telegraph # see LayerZero settings
    'mint_domain_ens'                  # 0.003 ETH domain
    'mint_domain_zns'                  # free domain
    'mint_mailzero'                    # mint free NFT on MainZero
    'mint_tevaera'                     # mint 2 NFT on Tevaera
    'mint_zerius'                      # mint NFT on Zerius
    'bridge_zerius'                    # bridge last NFT on Zerius
    'deploy_contract'                  # deploy your own contract
    'refuel_bungee'                    # see LayerZero settings
    'refuel_merkly'                    # see LayerZero settings
    'send_message_dmail'               
    'send_message_l2telegraph'         # see LayerZero settings
    'transfer_eth'                     
    'transfer_eth_to_myself'           
    'withdraw_txsync'                  
    'okx_deposit'                      
    'okx_collect_from_sub'             

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
    ['send_message_dmail'],
    # ['bridge_layerswap'],
    # ['mint_tevaera', 'mint_and_bridge_l2telegraph'],
    # ['enable_collateral_basilisk', 'enable_collateral_eralend', None],
    # ['swap_rango', 'swap_zkswap'],
    # ['refuel_merkly', 'swap_syncswap'],
    # ['mint_domain_zns', 'mint_domain_ens'],
    # ['wrap_eth', 'swap_pancake'],
    # ['swap_mute', 'swap_spacefi', 'swap_pancake'],
    # ['refuel_bungee', 'refuel_merkly'],
    # ['swap_oneinch', 'mint_domain_ens'],
    # ['mint_mailzero', 'swap_vesync'],
    # ['withdraw_txsync']
]


