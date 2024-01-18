"""
--------------------------------------------------OKX CONTROL-----------------------------------------------------------
    Выберите сети/суммы для вывода и ввода с OKX. Не забудьте вставить API ключи снизу.

    1 - ETH-ERC20              9  - CELO-Celo           17 - KLAY-Klaytn        26 - USDT-Arbitrum One
    2 - ETH-Arbitrum One       10 - ONE-Harmony         18 - FTM-Fantom         27 - USDC-ERC20
    3 - ETH-zkSync Lite        11 - GLMR-Moonbeam       19 - AVAX-Avalanche     28 - USDC-Optimism
    4 - ETH-Optimism           12 - MOVR-Moonriver      20 - ASTR-Astar         29 - USDC-Avalanche
    5 - ETH-Starknet           13 - METIS-Metis         21 - BNB-BSC            30 - USDC-Arbitrum One
    6 - ETH-zkSync Era         14 - CORE-CORE           22 - MATIC-Polygon      31 - USDC-Polygon
    7 - ETH-Linea              15 - CFX-Conflux         23 - USDT-Polygon       32 - USDC-Polygon (Bridged)
    8 - ETH-Base               16 - ZEN-Horizen         24 - USDT-Optimism      33 - USDC-Optimism (Bridged)
                                                        25 - USDT-Avalanche     34 - USDT-ERC20

------------------------------------------------------------------------------------------------------------------------
"""
OKX_WITHDRAW_NETWORK = 22      # Сеть вывода из OKX
OKX_WITHDRAW_AMOUNT = (1, 1)   # (минимальная, максимальная) сумма для вывода из OKX (кол-во)

OKX_MULTI_WITHDRAW = {  # Сеть вывода: (минимум, максимум) в токене для вывода (кол-во)
    9: (1, 1.011),
    4: (0.0001, 0.000111),
}

OKX_DEPOSIT_NETWORK = 32                  # Сеть из которой планируется пополнение OKX
OKX_DEPOSIT_AMOUNT = ('100', '100')    # (минимальная, максимальная) сумма для пополнения OKX (% или кол-во)

OKX_BALANCE_WANTED = 0.01               # Необходимый баланс на аккаунтах для уравнителя (make_balance_to_average)

"""
------------------------------------------------BRIDGE CONTROL----------------------------------------------------------
    Проверьте руками, работает ли сеть на сайте. (Софт сам проверит, но зачем его напрягать?)
    Софт работает только с нативным токеном(ETH). Не забудьте вставить API ключ для LayerSwap снизу.
    Для каждого моста поддерживается уникальная настройка
    
    Можно указать минимальную/максимальную сумму или минимальный/максимальный % от баланса
    
    Количество - (0.01, 0.02)
    Процент    - ("10", "20") ⚠️ Значения в скобках
       
     (A)Arbitrum = 1                    Polygon ZKEVM = 10 
        Arbitrum Nova = 2            (A)zkSync Era = 11     
     (A)Base = 3                       *Zora = 12 
        Linea = 4                       Ethereum = 13
        Manta = 5                      *Avalanche = 14
       *Polygon = 6                     BNB Chain = 15
     (A)Optimism = 7                 (O)Metis = 26        
        Scroll = 8                     *OpBNB = 28
        Starknet = 9                   *Mantle = 29
                                        ZKFair = 45   
    
    * - не поддерживается в Rhino.fi
    (A) - сети, поддерживаемые Across мостом
    (0) - поддерживается только для Orbiter моста
    ORBITER_CHAIN_ID_FROM(TO) = [2, 4, 16] | Одна из сетей будет выбрана
    NATIVE_WITHDRAW_AMOUNT | Настройка для вывода из нативного моста (withdraw_native_bridge)
"""
NATIVE_DEPOSIT_AMOUNT = (0.002, 0.002)    # (минимум, максимум) (% или кол-во)
NATIVE_WITHDRAW_AMOUNT = (0.0001, 0.0002)   # (минимум, максимум) (% или кол-во)

ORBITER_CHAIN_ID_FROM = [7]                # Исходящая сеть
ORBITER_CHAIN_ID_TO = [45]                  # Входящая сеть
ORBITER_DEPOSIT_AMOUNT = (1, 1)          # (минимум, максимум) (% или кол-во)
ORBITER_TOKEN_NAME = 'USDC'

LAYERSWAP_CHAIN_ID_FROM = [1]                # Исходящая сеть
LAYERSWAP_CHAIN_ID_TO = [4]                  # Входящая сеть
LAYERSWAP_DEPOSIT_AMOUNT = (0.002, 0.002)    # (минимум, максимум) (% или кол-во)

RHINO_CHAIN_ID_FROM = [1]                # Исходящая сеть
RHINO_CHAIN_ID_TO = [11]                  # Входящая сеть
RHINO_DEPOSIT_AMOUNT = (0.012, 0.022)    # (минимум, максимум) (% или кол-во)

ACROSS_CHAIN_ID_FROM = [9]                # Исходящая сеть
ACROSS_CHAIN_ID_TO = [4]                  # Входящая сеть
ACROSS_DEPOSIT_AMOUNT = (0.002, 0.002)    # (минимум, максимум) (% или кол-во)

"""
---------------------------------------------OMNI-CHAIN CONTROL---------------------------------------------------------
    Проверьте руками, работают ли сети на сайте. (Софт сам проверит, но зачем его напрягать?)
       
     (B)Arbitrum = 1                  Goerli = 16                        OKX = 30
        Arbitrum Nova = 2             Gnosis = 17                     (B)Optimism = 31
        Astar = 3                     Harmony = 18                       Orderly = 32
     (B)Aurora = 4                    Horizen = 19                    (B)Polygon = 33  
     (B)Avalanche = 5                 Kava = 20                       (B)Polygon zkEVM = 34
        BNB = 6                       Klaytn = 21                        Scroll = 35
     (B)Base = 7                      Linea = 22                         ShimmerEVM = 36
        Canto = 8                     Loot = 23                          Telos = 37
        Celo = 9                      Manta = 24                         TomoChain = 38 
        Conflux = 10                  Mantle = 25                        Tenet = 39
        CoreDAO = 11                  Meter = 26                         XPLA = 40
        DFK = 12                      Metis = 27                         Zora = 41  
        Ethereum = 13                 Moonbeam = 28                      opBNB = 42
        Fantom = 14                   Moonriver = 29                     zkSync = 43
        Fuse = 15                                                        Beam = 44

    STARGATE_CHAINS | Выберите чейны, между которыми будут производиться бриджи
    STARGATE_TOKENS | Выберите монеты, между которыми будут производиться свапы. Доступны: ETH, USDT, USDC. 
        Токены указывать в таком же порядке, как и чейны. Условно STARGATE_CHAINS = [5, 6] и
        STARGATE_TOKENS = ['USDC', 'USDT'] будет означать, что для 5 чейна будет USDC, а для 6 USDT
    
    STARGATE_SWAPS_AMOUNT | Количество бриджей внутри модуля stargate_volume
    
    COREDAO_CHAINS | Аналогично STARGATE_CHAINS
    COREDAO_TOKENS | Аналогично STARGATE_TOKENS
    
    SRC_CHAIN_BUNGEE = [27, 29]        
    SRC_CHAIN_ZERIUS = [27, 29] 
    SRC_CHAIN_MERKLY = [27, 29] 
    SRC_CHAIN_L2PASS = [27, 29] | Одна из сетей будет выбрана (REFUEL/BRIDGE NFT(включая Wormhole на Merkly))
    
    DST_CHAIN_MERKLY_REFUEL = {
        1: (0.0016, 0.002), # Chain ID: (минимум, максимум) в нативном токене входящей сети**
        2: (0.0002, 0.0005) 
    } 
    
    WORMHOLE_TOKENS_AMOUNT | Количество токенов для минта и бриджа через Wormhole
    
    DST_CHAIN_L2PASS_REFUEL 
    DST_CHAIN_BUNGEE_REFUEL
    DST_CHAIN_ZERIUS_REFUEL | Аналогично DST_CHAIN_MERKLY_REFUEL
    
    SRC_CHAIN_L2TELEGRAPH | Исходящая сеть для L2Telegraph
    DST_CHAIN_L2TELEGRAPH | Входящая сеть для L2Telegraph 
    
    ZERIUS_ATTACK_REFUEL
    MERKLY_ATTACK_REFUEL
    L2PASS_ATTACK_REFUEL | Указываете в списках вариант refuel (исходящая сеть, входящая сеть, мин. сумму к refuel). 
    
    ZERIUS_ATTACK_NFT
    L2PASS_ATTACK_NFT | Указываете в списках вариант бриджа NFT (исходящая сеть, входящая сеть). 
                           
    SHUFFLE_ATTACK | Если стоит True, то софт перемешает маршрут атаки 
    WAIT_FOR_RECEIPT | Если стоит True, то софт будет ждать получения средств во входящей сети, перед запуском модуля
                        следующего модуля
    
    MERKLY_ATTACK_REFUEL = [
    ([43, 3, 0.0001], None),  # Пример использования рандомной атаки: (данные для атаки, None). Если будет выбран None,
    ]                                 то модуль будет пропущен 
    
    (B) - Поддерживаемые входящие сети в Bungee
    Сумму для Merkly и Zerius нужно подавать в нативном токене входящей сети. Указывайте на 10% меньше от лимита,
    во избежания ошибок работы LayerZero мостов. Смотреть лимиты можно здесь: 
            1) Zerius - https://zerius.io/refuel
            2) Merkly - https://minter.merkly.com/gas  
"""
STARGATE_CHAINS = [1, 7, 22, 31]
STARGATE_TOKENS = ['ETH', 'ETH', 'ETH', 'ETH']
STARGATE_SWAPS_AMOUNT = 4       # применяется для stargate_volume

COREDAO_CHAINS = [33, 11]
COREDAO_TOKENS = ['USDC', 'USDT']

SRC_CHAIN_ZERIUS = [1]          # Исходящая сеть для Zerius
DST_CHAIN_ZERIUS_NFT = [4]     # Входящая сеть для Zerius Mint NFT
DST_CHAIN_ZERIUS_REFUEL = {
    1: (0.0001, 0.0002),        # Chain ID: (минимум, максимум) в нативном токене входящей сети (кол-во)
    4: (0.0001, 0.0002)
}

SRC_CHAIN_MERKLY_WORMHOLE = [7]   # Исходящая сеть для Merkly Wormhole
DST_CHAIN_MERKLY_WORMHOLE = [9, 14, 21, 28]   # Входящая сеть для Merkly Wormhole
WORMHOLE_TOKENS_AMOUNT = 1        # Кол-во токенов для минта и бриджа на Merkly через Wormhole

SRC_CHAIN_MERKLY = [43]            # Исходящая сеть для Merkly
DST_CHAIN_MERKLY_REFUEL = {
     3: (0.000001, 0.00002),        # Chain ID: (минимум, максимум) в нативном токене входящей сети (кол-во)
    17: (0.000001, 0.00002),
    20: (0.000001, 0.00002),
    21: (0.000001, 0.00002),
}

SRC_CHAIN_L2PASS = [1]          # Исходящая сеть для L2PASS
DST_CHAIN_L2PASS_NFT = [6]     # Входящая сеть для L2PASS Mint NFT
DST_CHAIN_L2PASS_REFUEL = {
    20: (0.000001, 0.00002),        # Chain ID: (минимум, максимум) в нативном токене входящей сети (кол-во)
    28: (0.000001, 0.00002),
    29: (0.000001, 0.00002),
}

SRC_CHAIN_BUNGEE = [43]          # Исходящая сеть для Bungee
DST_CHAIN_BUNGEE_REFUEL = {
    17:  (0.00005, 0.000006),        # Chain ID: (минимум, максимум) в ETH (кол-во)
}

SRC_CHAIN_L2TELEGRAPH = [43]    # Исходящая сеть для L2Telegraph.
DST_CHAIN_L2TELEGRAPH = [2]    # Входящая сеть для L2Telegraph.

'---------------------------------------------LAYERZERO ATTACKS--------------------------------------------------------'

WAIT_FOR_RECEIPT = True  # Если True, будет ждать получения средств во входящей сети перед запуском очередного модуля
SHUFFLE_ATTACK = True     # Если True, то перемешает маршрут для атаки перед стартом

ZERIUS_ATTACK_REFUEL = [
    [43, 3, 0.0001],
    [33, 5, 0.0001],
    [21, 6, 0.0001],
    [12, 8, 0.0001],
]

ZERIUS_ATTACK_NFT = [
    [43, 3],
    [3, 5],
    [5, 6],
    [6, 8],
]

MERKLY_ATTACK_REFUEL = [
    ([43, 3, 0.0001], None),
    [33, 5, 0.0001],
    [21, 6, 0.0001],
    [12, 8, 0.0001],
]


L2PASS_ATTACK_REFUEL = [
    [33, 18, 4],
]

L2PASS_ATTACK_NFT = [
    [17, 18],
    [3, 5],
    [5, 6],
    [6, 8],
]

"""
--------------------------------------------------OTHER SETTINGS--------------------------------------------------------

    STARKSTARS_NFT_CONTRACTS | Укажите какие NFT ID будут участвовать в минте. Все что в скобках, будут использованы
    ZKSTARS_NFT_CONTRACTS | Укажите какие NFT ID будут участвовать в минте. Все что в скобках, будут использованы
    NEW_WALLET_TYPE | Определяет какой кошелек будет задеплоен, если вы решили создать новый. 0 - ArgentX | 1 - Braavos
    MINTFUN_CONTRACTS | Список контрактов для минта в выбранной сети (GLOBAL NETWORK)
    
    GRAPEGRAW_TICKETS_AMOUNT | Количество билетов для покупки в одной транзакции на сайте https://grapegraw.io
    
    INSCRIPTION_DATA | Указывайте дату для минта. Обычно ее дают на сайтах. Поддерживаются форматы в виде json и hex.
        В формате json - 'data....'
        В формате hex - 0x123
    INSCRIPTION_NETWORK | Сеть в которой планируется минтить инскрипшен. Поддерживаются все сети из OMNI-CHAIN CONTROL    
    
    MEMCOIN_AMOUNT | Сумма в ETH, на которую планируете покупать мемкоин.
"""

STARKSTARS_NFT_CONTRACTS = (1, 2, 3, 4)  # при (0) заминтит случайную новую NFT
ZKSTARS_NFT_CONTRACTS = (1, 2, 3, 4)  # при (0) заминтит случайную новую NFT
NEW_WALLET_TYPE = 1

GRAPEDRAW_TICKETS_AMOUNT = 1

INSCRIPTION_DATA = ''
INSCRIPTION_NETWORK = 0

MEMCOIN_AMOUNT = 0.01  # сумма в ETH

ZKFAIR_STAKE_PERIOD = 90  # кол-во дней для стейкинга (месяц = 30)
ZKFAIR_STAKE_AMOUNT = 50  # процент от баланса ZKF для стейкинга
ZKFAIR_CLAIM_REFUND_PHASES = [1, 2, 3, 4]  # фазы для клейма рефаунда

MINTFUN_CONTRACTS = {
    '0x123': 0,
    '0x1234': 0.0001,
    '0x12345': 0.00003
}

"""
----------------------------------------------GOOGLE-ROUTES CONTROL-----------------------------------------------------
    Технология сохранения прогресса для каждого аккаунта с помощью Google Spreadsheets 
    При каждом запуске, софт будет брать информацию из Google таблицы и настроек снизу, для генерации уникального
     маршрута под каждый аккаунт в таблице.  
    ⚠️Количество аккаунтов и их расположение должно быть строго одинаковым для вашего Excel и Google Spreadsheets⚠️
                                                         
    DEPOSIT_CONFIG | Включает в маршрут для каждого аккаунта модули, со значениями '1'
                     'okx_withdraw' всегда будет первой
                     Бриджи всегда после 'okx_withdraw'
                     'okx_deposit' и 'okx_collect_from_sub' всегда последние
    
"""

DMAIL_IN_ROUTES = False        # True или False | Включает Dmail в маршрут
TRANSFER_IN_ROUTES = False     # True или False | Включает трансферы в маршрут
COLLATERAL_IN_ROUTES = False   # True или False | Включает случайное вкл/выкл страховки в маршрут

DMAIL_COUNT = (1, 1)          # (минимум, максимум) дополнительных транзакций для Dmail
TRANSFER_COUNT = (1, 2)       # (минимум, максимум) дополнительных транзакций для трансферов
COLLATERAL_COUNT = (1, 2)     # (минимум, максимум) дополнительных транзакций для вкл/выкл страхования

MODULES_COUNT = (1, 2)        # (минимум, максимум) неотработанных модулей из Google таблицы
ALL_MODULES_TO_RUN = False     # True или False | Включает все неотработанные модули в маршрут
WITHDRAW_LP = False            # True или False | Включает в маршрут все модули для вывода ликвидности из DEX
WITHDRAW_LANDING = False      # True или False | Включает в маршрут все модули для вывода ликвидности из лендингов
HELP_NEW_MODULE = False        # True или False | Добавляет случайный модуль при неудачном выполнении модуля из маршрута
EXCLUDED_MODULES = ['swap_openocean']  # Исключает выбранные модули из маршрута. Список в Classic-Routes

HELPERS_CONFIG = {
    'okx_withdraw'                        : 0,  # смотри OKX CONTROL
    'okx_multi_withdraw'                  : 0,  # вывод в несколько сетей. Смотри OKX CONTROL (OKX_MULTI_WITHDRAW)
    'collector_eth'                       : 0,  # сбор всех токенов в ETH внутри сети GLOBAL_NETWORK
    'make_balance_to_average'             : 0,  # уравнивает ваши балансы на аккаунтах (см. инструкцию к софту)
    'upgrade_stark_wallet'                : 0,  # обновляет кошелек, во время маршрута
    'deploy_stark_wallet'                 : 0,  # деплоит кошелек, после вывода с OKX
    'bridge_across'                       : 0,  # смотри BRIDGE CONTROL
    'bridge_rhino'                        : 0,  # смотри BRIDGE CONTROL
    'bridge_layerswap'                    : 0,  # смотри BRIDGE CONTROL
    'bridge_orbiter'                      : 0,  # смотри BRIDGE CONTROL
    'bridge_native'                       : 0,  # смотри BRIDGE CONTROL
    'okx_deposit'                         : 0,  # ввод средств на биржу
    'okx_collect_from_sub'                : 0   # сбор средств на субАккаунтов на основной счет
}

"""
--------------------------------------------CLASSIC-ROUTES CONTROL------------------------------------------------------

---------------------------------------------------HELPERS--------------------------------------------------------------        

    okx_withdraw                     # смотри OKX CONTROL
    okx_multi_withdraw               # вывод в несколько сетей. Смотри OKX CONTROL (OKX_MULTI_WITHDRAW)
    random_okx_withdraw              # вывод в рандомную сеть из OKX_MULTI_WITHDRAW
    collector_eth                    # сбор всех токенов в ETH
    make_balance_to_average          # уравнивает ваши балансы на аккаунтах (см. инструкцию к софту) 
    upgrade_stark_wallet             # обновляет кошелек, во время маршрута
    deploy_stark_wallet              # деплоит кошелек, после вывода с OKX
    bridge_across                    # смотри BRIDGE CONTROL
    bridge_rhino                     # смотри BRIDGE CONTROL
    bridge_layerswap                 # смотри BRIDGE CONTROL
    bridge_orbiter                   # смотри BRIDGE CONTROL
    bridge_native                    # смотри BRIDGE CONTROL. (кол-во из NATIVE_DEPOSIT_AMOUNT)
    okx_deposit                      # ввод средств на биржу
    okx_collect_from_sub             # сбор средств на субАккаунтов на основной счет
    
---------------------------------------------------CUSTOM---------------------------------------------------------------        
    
    mint_token_avnu                  # обмен щитка на AVNU. Сумма в ETH - MEMCOIN_AMOUNT. Контракт менять в config.py
    mint_token_jediswap              # обмен щитка на JediSwap. Контракт в config.py - TOKENS_PER_CHAIN (Starknet)   
    mint_scroll_nft                  # минт Scroll NFT за деплой контрактов
    mint_inscription                 # минт инскрипшена в сети INSCRIPTION_NETWORK(номера из L0).
    zksync_rhino_checker             # проверка на eligible для минта Rhino.fi Pro Hunter NFT 
    zksync_rhino_mint                # минт Rhino.fi Hunter NFT
    zksync_rhino_mint_pro            # проверка на eligible и минт Rhino.fi Pro Hunter NFT
    claim_refund_zkfair              # клейм рефанда за участие в раздаче ZKFair. см. ZKFAIR_CLAIM_REFUND_PHASES
    stake_zkfair                     # стейкинг токена ZKF в сети ZKFair. см. ZKFAIR_STAKE_PERIOD, ZKFAIR_STAKE_AMOUNT
    
--------------------------------------------------LAYERZERO-------------------------------------------------------------            
    
    mint_zerius                      # mint NFT on Zerius. Price: уточняйте по факту на сайте.
    mint_l2pass                      # mint NFT on L2Pass. Price: уточняйте по факту на сайте.
    bridge_zerius                    # bridge последней NFT on Zerius
    bridge_l2pass                    # bridge последней NFT on L2Pass
    refuel_merkly                    # смотри OMNI-CHAIN CONTROL
    refuel_zerius                    # смотри OMNI-CHAIN CONTROL
    refuel_l2pass                    # смотри OMNI-CHAIN CONTROL
    refuel_bungee                    # смотри OMNI-CHAIN CONTROL
    smart_merkly                     # автоматический поиск доступного пути для refuel. настройки из refuel_merkly
    smart_l2pass                     # автоматический поиск доступного пути для refuel. настройки из refuel_l2pass
    smart_zerius                     # автоматический поиск доступного пути для refuel. настройки из refuel_zerius
    mint_and_bridge_l2telegraph      # mint и bridge NFT через L2Telegraph. См. OMNI-CHAIN CONTROLE
    send_message_l2telegraph         # смотри OMNI-CHAIN CONTROL
    stargate_volume                  # выводит из рандомной сети OKX_MULTI_WITHDRAW -> бриджи на Stargate -> деп на OKX
    bridge_stargate                  # бриджи на Stargate. STARGATE_CHAINS, STARGATE_TOKENS. См. OMNI-CHAIN CONTROLE
    bridge_coredao                   # бриджи на CoreDAO. COREDAO_CHAINS, COREDAO_TOKENS. См. OMNI-CHAIN CONTROLE
    zerius_refuel_attack             # Refuel атака на Zerius. Делает много рефьелов в разные сети. См. OMNI-CHAIN CONTROLE
    merkly_refuel_attack             # Refuel атака на Merkly.      
    l2pass_refuel_attack             # Refuel атака на L2Pass.
    zerius_nft_attack                # NFT Bridge атака на Zerius.
    l2pass_nft_attack                # NFT Bridge атака на L2Pass.    
    
---------------------------------------------------WORMHOLE-------------------------------------------------------------            

    mint_and_bridge_wormhole_nft     # минт и бридж NFT на Merkly через Wormhole 
    mint_and_bridge_wormhole_token   # минт и бридж токенов на Merkly через Wormhole 
    
----------------------------------------------------ZKSYNC--------------------------------------------------------------        

    add_liquidity_maverick           # USDC/WETH LP
    add_liquidity_mute               # USDC/WETH LP
    add_liquidity_syncswap           # USDC/WETH LP на LIQUIDITY_AMOUNT
    deposit_basilisk                 # делает депозит в лендинг на LIQUIDITY_AMOUNT
    deposit_eralend                  
    deposit_reactorfusion            
    deposit_zerolend                 
    enable_collateral_basilisk       # включает страховку для депозита на лендинге
    enable_collateral_eralend        
    enable_collateral_reactorfusion  
    swap_izumi                       # делает случайный свап токенов на AMOUNT_PERCENT для ETH и на 100% для других.
    swap_maverick                      пары выбираются случайно, с учетом баланса на кошельке. Свапы работаю по
    swap_mute                          следующим направлениям: ETH -> Token, Token -> ETH. Token -> Token не будет, во
    swap_odos                          избежания проблем с платой за газ.
    swap_oneinch                     
    swap_openocean                   
    swap_pancake                     
    swap_rango                       
    swap_spacefi                     
    swap_syncswap                    
    swap_velocore                    
    swap_xyfinance                   
    swap_vesync                      
    swap_woofi                       
    swap_zkswap                 
    wrap_eth                         # wrap/unwrap ETH через офф. контракт токена WETH. (кол-во из LIQUIDITY_AMOUNT)
    grapedraw_bid                    # создание ставки на GrapeDraw. см. GRAPEDRAW_TICKETS_AMOUNT
    create_omnisea                   # создание новой NFT коллекции. Все параметры будут рандомными
    create_safe                      # создает сейф в сети GLOBAL_NETWORK
    mint_domain_ens                  # 0.003 ETH domain
    mint_domain_zns                  # 0.003 ETH domain
    mint_mailzero                    # mint бесплатной NFT на MailZero. Плата только за газ.
    mint_tevaera                     # mint 2 NFT on Tevaera. Price: 0.0003 ETH
    deploy_contract                  # deploy вашего контракта. Контракт находится в data/services/contract_data.json
    random_approve                   # рандомный апрув случайного токена для свапалок 
    send_message_dmail               # отправка сообщения через Dmail на рандомный Web2 адрес (почтовый ящик)
    transfer_eth                     # переводит (TRANSFER_AMOUNT) ETH на случайный адрес
    transfer_eth_to_myself           # переводит (TRANSFER_AMOUNT) ETH на ваш адрес
    wrap_abuser                      # свапы ETH-WETH через контракты агрегаторов. (кол-во из AMOUNT_PERCENT_WRAPS)     
    withdraw_native_bridge           # вывод ETH через официальный мост. (кол-во из NATIVE_WITHDRAW_AMOUNT)
    withdraw_basilisk                # вывод ликвидности из лендинга
    withdraw_eralend                 
    withdraw_reactorfusion           
    withdraw_zerolend                
    disable_collateral_basilisk      # выключение страховки депозита на лендинге
    disable_collateral_eralend       
    disable_collateral_reactorfusion 
    withdraw_liquidity_maverick      # выводит всю ликвидность из пула USDC/WETH
    withdraw_liquidity_mute
    withdraw_liquidity_syncswap
                  
----------------------------------------------------STARKNET------------------------------------------------------------        
    
    upgrade_stark_wallet            
    deploy_stark_wallet     
    deposit_nostra                 
    deposit_zklend                 
    swap_jediswap                   
    swap_avnu
    swap_10kswap
    swap_sithswap
    swap_protoss
    swap_myswap
    send_message_dmail
    random_approve
    transfer_eth                     
    transfer_eth_to_myself   
    wrap_abuser                     
    enable_collateral_zklend
    disable_collateral_zklend
    mint_starknet_identity
    mint_starkstars
    withdraw_nostra
    withdraw_zklend
    withdraw_native_bridge
    
------------------------------------------------------BASE--------------------------------------------------------------        

    swap_pancake
    swap_uniswap
    swap_sushiswap
    swap_woofi
    swap_maverick
    swap_izumi
    swap_odos
    swap_oneinch
    swap_openocean
    swap_xyfinance
    deposit_rocketsam
    withdraw_rocketsam
    create_safe
    mint_mintfun
    mint_zkstars
    deploy_contract
    random_approve
    transfer_eth                     
    transfer_eth_to_myself
    wrap_abuser                      
    send_message_dmail

------------------------------------------------------LINEA-------------------------------------------------------------        

    swap_syncswap
    swap_pancake
    swap_woofi
    swap_velocore
    swap_izumi
    swap_rango
    swap_openocean
    swap_xyfinance
    deposit_layerbank
    withdraw_layerbank
    deposit_rocketsam
    withdraw_rocketsam
    create_omnisea
    mint_zkstars
    deploy_contract
    random_approve
    transfer_eth                     
    transfer_eth_to_myself
    wrap_abuser                     
    send_message_dmail

-------------------------------------------------------SCROLL-----------------------------------------------------------        

    swap_syncswap
    swap_spacefi
    swap_izumi
    swap_openocean
    swap_xyfinance
    deposit_layerbank
    withdraw_layerbank
    deposit_rocketsam
    withdraw_rocketsam
    create_omnisea
    mint_zkstars
    deploy_contract
    random_approve
    transfer_eth                     
    transfer_eth_to_myself   
    send_message_dmail
    wrap_abuser                     
    withdraw_native_bridge
    
--------------------------------------------------------ZORA------------------------------------------------------------        
    
    mint_mintfun
    mint_zkstars
    deposit_rocketsam
    wrap_abuser                           
    transfer_eth                     
    transfer_eth_to_myself

--------------------------------------------------------NOVA------------------------------------------------------------        
    
    swap_sushiswap
    deposit_rocketsam
    wrap_abuser                          
    transfer_eth                     
    transfer_eth_to_myself
    
    Роуты для настоящих древлян (Машина - зло).
    Выберите необходимые модули для взаимодействия
    Вы можете создать любой маршрут, софт отработает строго по нему. Для каждого списка будет выбран один модуль в
    маршрут, если софт выберет None, то он пропустит данный список модулей. 
    Список модулей сверху.
    
    CLASSIC_ROUTES_MODULES_USING = [
        ['okx_withdraw'],
        ['bridge_layerswap', 'bridge_native'],
        ['swap_mute', 'swap_izumi', 'mint_domain_ens', None],
        ...
    ]
"""
CLASSIC_ROUTES_MODULES_USING = [
    ['okx_withdraw'],
    ['bridge_layerswap', 'bridge_native'],
    ['swap_mute', 'swap_izumi', 'mint_domain_ens', None],
]
