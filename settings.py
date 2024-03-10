"""
----------------------------------------------------CEX CONTROL---------------------------------------------------------
    Выберите сети/суммы для вывода и ввода с CEX. Не забудьте вставить API ключи в general_settings.py.
    Депозиты и выводы работают только со спотовым балансом на бирже.

    1 - ETH-ERC20                10 - CELO-CELO           19 - USDT-Arbitrum One       29 - USDC-Optimism (Bridged)
    2 - ETH-Arbitrum One         11 - GLMR-Moonbeam       20 - USDT-Avalanche          30 - USDC-Polygon (Bridged)
    3 - ETH-Optimism             12 - MOVR-Moonriver      21 - USDT-Optimism           31 - USDC-BSC
    4 - ETH-zkSync Era           13 - METIS-Metis         22 - USDT-Polygon            32 - USDC-ERC20
    5 - ETH-Linea                14 - CORE-CORE           23 - USDT-BSC                33 - STG-Arbitrum One
    6 - ETH-Base                 15 - CFX-CFX_EVM         24 - USDT-ERC20              34 - STG-BSC
    7 - AVAX-Avalanche C-Chain   16 - KLAY-Klaytn         25 - USDC-Arbitrum One       35 - STG-Avalanche C-Chain
    8 - BNB-BSC                  17 - FTM-Fantom          26 - USDC-Avalanche C-Chain  36 - STG-Fantom
    9 - BNB-OPBNB                18 - MATIC-Polygon       27 - USDC-Optimism           37 - USDV-BSC
                                                          28 - USDC-Polygon            38 - ARB-Arbitrum One

    Сумма в количестве  - (0.01, 0.02)
    Сумма в процентах   - ("10", "20") ⚠️ Значения в кавычках

    OKX_WITHDRAW_DATA | Каждый список - один модуль для вывода из биржи. Примеры работы указаны ниже:
                        Для каждого вывода указывайте [сеть вывода, (мин и макс сумма)]

    OKX_DEPOSIT_DATA | Каждый список - один модуль для депозита на биржу. Примеры работы указаны ниже:
                       Для каждого вывода указывайте [сеть депозита, (мин и макс сумма)]

    Примеры рандомизации:

    [[17, (1, 1.011)], None] | Пример установки None, для случайного выбора (выполнение действия или его пропуск)
    [[2, (0.48, 0.5)], [3, (0.48, 0.5)]] | Пример установки двух сетей, софт выберет одну случайную.
    [(2, 3, 4), (0.001, 0.002)] | Пример указания нескольких сетей, cофт выберет сеть с наибольшим балансом.

    CEX_DEPOSIT_LIMITER | Настройка лимитного вывода на биржу. Указывать в $USD
                          1 значение - это минимальный баланс на аккаунте, чтобы софт начал процесс вывода
                          2 значение - это мин. и макс. сумма, которая должна остаться на балансе после вывода.
                          Если сумма депозита будет оставлять баланс на аккаунте больше 2-го значения, софт не будет
                          пытать сделать сумму депозита больше или меньше указанной в DEPOSIT_DATA

    CEX_BALANCE_WANTED | Софт выведет средства с биржи таким образом, чтобы уровнять баланс аккаунта к этой настройке
                         Модуль (make_balance_to_average). Указывать в ETH, запускать для сети в GLOBAL_NETWORK.
                         1 значение - биржа для вывода. 1 - OKX, 2 - BingX, 3 - Binance, 4 - Bitget
                         2 значение - это мин. и макс. сумма, к которой нужно прировнять балансы на аккаунтах
"""
'--------------------------------------------------------OKX-----------------------------------------------------------'

OKX_WITHDRAW_DATA = [
    [18, (3.2, 3.3)],
]

OKX_DEPOSIT_DATA = [
    [6, (0.0001, 0.0002)],
]

'--------------------------------------------------------BingX---------------------------------------------------------'

BINGX_WITHDRAW_DATA = [
    [2, (0.0007, 0.00071)],
]

BINGX_DEPOSIT_DATA = [
    [4, (0.001, 0.00011)],
]

'-------------------------------------------------------Binance--------------------------------------------------------'

BINANCE_WITHDRAW_DATA = [
    [8, (0.004, 0.00411)],
]

BINANCE_DEPOSIT_DATA = [
    [3, (0.001, 0.001)]
]

'--------------------------------------------------------BitGet--------------------------------------------------------'

BITGET_WITHDRAW_DATA = [
    [8, (0.004, 0.00411)],
]

BITGET_DEPOSIT_DATA = [
    [3, (0.001, 0.001)]
]

'-------------------------------------------------------Control--------------------------------------------------------'

CEX_BALANCE_WANTED = 1, (0.01, 0.01)    # Необходимый баланс на аккаунтах для уравнителя (make_balance_to_average)
CEX_DEPOSIT_LIMITER = 0, (0, 0)         # (Ограничитель баланса, (мин. сумма, макс. сумма для остатка на балансе))

"""
-----------------------------------------------------BRIDGE CONTROL-----------------------------------------------------
    Проверьте руками, работает ли сеть на сайте. (Софт сам проверит, но зачем его напрягать?)
    Не забудьте вставить API ключ для LayerSwap снизу. Для каждого моста поддерживается уникальная настройка
       
        Arbitrum = 1                    zkSync Era = 11     
        Arbitrum Nova = 2               Zora = 12 
        Base = 3                        Ethereum = 13
        Linea = 4                       Avalanche = 14
        Manta = 5                       BNB Chain = 15
        Polygon = 6                     Metis = 26        
        Optimism = 7                    OpBNB = 28
        Scroll = 8                      Mantle = 29
        Starknet = 9                    ZKFair = 45
        Polygon ZKEVM = 10              Blast = 49
                                           
    Сумма в количестве  - (0.01, 0.02)
    Сумма в процентах   - ("10", "20") ⚠️ Значения в кавычках
    
    NATIVE_CHAIN_ID_FROM(TO) = [2, 4, 16] | Одна из сетей будет выбрана. Применимо для bridge_zora (instant), 
                                            остальные бриджи в L2 будут из Ethereum, а выводы в Ethereum
    NATIVE_WITHDRAW_AMOUNT | Настройка для вывода из нативного моста (withdraw_native_bridge)
    ACROSS_TOKEN_NAME | Укажите токен для бриджа. Поддерживаются: ETH, BNB, MATIC, USDC, USDC.e (Bridged), USDT. 
                        Если у бриджа указано 2 токена в скобках см. BUNGEE_TOKEN_NAME, то бридж сможет делать бриджи
                        между разными токенами. Справа от параметра, для каждого бриджа указаны доступные токены.
                        
    BRIDGE_AMOUNT_LIMITER | Настройка лимитных бриджей. Указывать в $USD
                            1 значение - это минимальный баланс на аккаунте, чтобы софт начал процесс бриджа
                            2 значение - это мин. и макс. сумма, которая должна остаться на балансе после бриджа
                            Если сумма для бриджа будет оставлять баланс на аккаунте больше второго значения,
                            софт не будет пытать сделать сумму бриджа больше или меньше указанной
                            
    BUNGEE_ROUTE_TYPE | Установка своего роута для совершения транзакции, по умолчанию (0) - самый лучший. 
                        1-Across   3-Celer     5-Stargate   7-Synapse      9-Hop
                        2-CCTP     4-Connext   6-Socket     8-Symbiosis    10-Hyphen   
                                                      
"""

'-----------------------------------------------------Native Bridge----------------------------------------------------'

NATIVE_CHAIN_ID_FROM = [1]                # Исходящая сеть. 21.01.2024 Применимо только для bridge_zora
NATIVE_CHAIN_ID_TO = [12]                  # Входящая сеть. 21.01.2024 Применимо только для bridge_zora
NATIVE_BRIDGE_AMOUNT = (0.001, 0.001)      # (минимум, максимум) (% или кол-во)
NATIVE_WITHDRAW_AMOUNT = (0.0001, 0.0002)  # (минимум, максимум) (% или кол-во)

'--------------------------------------------------------Across--------------------------------------------------------'

ACROSS_CHAIN_ID_FROM = [9]                # Исходящая сеть
ACROSS_CHAIN_ID_TO = [4]                  # Входящая сеть
ACROSS_BRIDGE_AMOUNT = (0.002, 0.002)     # (минимум, максимум) (% или кол-во)
ACROSS_TOKEN_NAME = 'ETH'

'--------------------------------------------------------Bungee--------------------------------------------------------'

BUNGEE_CHAIN_ID_FROM = [3]                  # Исходящая сеть
BUNGEE_CHAIN_ID_TO = [1]                    # Входящая сеть
BUNGEE_BRIDGE_AMOUNT = (0.001, 0.001)               # (минимум, максимум) (% или кол-во)
BUNGEE_TOKEN_NAME = ('ETH', 'ETH')       # ETH, BNB, MATIC, USDC, USDC.e, USDT
BUNGEE_ROUTE_TYPE = 5                       # см. BUNGEE_ROUTE_TYPE

'-------------------------------------------------------LayerSwap------------------------------------------------------'

LAYERSWAP_CHAIN_ID_FROM = [11]               # Исходящая сеть
LAYERSWAP_CHAIN_ID_TO = [7]                  # Входящая сеть
LAYERSWAP_BRIDGE_AMOUNT = (0.001, 0.001)     # (минимум, максимум) (% или кол-во)
LAYERSWAP_TOKEN_NAME = ('USDC.e', 'ETH')     # ETH, USDC, USDC.e

'--------------------------------------------------------Nitro---------------------------------------------------------'

NITRO_CHAIN_ID_FROM = [1]                   # Исходящая сеть
NITRO_CHAIN_ID_TO = [11]                    # Входящая сеть
NITRO_BRIDGE_AMOUNT = (0.001, 0.001)        # (минимум, максимум) (% или кол-во)
NITRO_TOKEN_NAME = ('ETH', 'USDC')          # ETH, USDC, USDT

'-------------------------------------------------------Orbiter--------------------------------------------------------'

ORBITER_CHAIN_ID_FROM = [7, 3, 5]           # Исходящая сеть
ORBITER_CHAIN_ID_TO = [6]                   # Входящая сеть
ORBITER_BRIDGE_AMOUNT = (8, 9)              # (минимум, максимум) (% или кол-во)
ORBITER_TOKEN_NAME = 'USDC'

'--------------------------------------------------------Owlto---------------------------------------------------------'

OWLTO_CHAIN_ID_FROM = [11]                 # Исходящая сеть
OWLTO_CHAIN_ID_TO = [4]                    # Входящая сеть
OWLTO_BRIDGE_AMOUNT = (0.002, 0.003)       # (минимум, максимум) (% или кол-во)
OWLTO_TOKEN_NAME = 'ETH'

'--------------------------------------------------------Relay---------------------------------------------------------'

RELAY_CHAIN_ID_FROM = [11]                # Исходящая сеть
RELAY_CHAIN_ID_TO = [7]                   # Входящая сеть
RELAY_BRIDGE_AMOUNT = (0.001, 0.001)      # (минимум, максимум) (% или кол-во)
RELAY_TOKEN_NAME = 'ETH'

'--------------------------------------------------------Rhino---------------------------------------------------------'

RHINO_CHAIN_ID_FROM = [7]                # Исходящая сеть
RHINO_CHAIN_ID_TO = [11]                 # Входящая сеть
RHINO_BRIDGE_AMOUNT = (1, 1.8)           # (минимум, максимум) (% или кол-во)
RHINO_TOKEN_NAME = ('USDC', 'ETH')       # ETH, BNB, MATIC, USDC, USDT

'-------------------------------------------------------Control--------------------------------------------------------'

BRIDGE_AMOUNT_LIMITER = 0, (0, 0)  # (Ограничитель баланса, (мин. сумма, макс. сумма для остатка на балансе))

"""
---------------------------------------------OMNI-CHAIN CONTROL---------------------------------------------------------
    Проверьте руками, работают ли сети на сайте. (Софт сам проверит, но зачем его напрягать?)
       
        Arbitrum = 1                  Goerli = 16                        Optimism = 31
        Arbitrum Nova = 2             Gnosis = 17                        Orderly = 32
        Astar = 3                     Harmony = 18                       Polygon = 33  
        Aurora = 4                    Horizen = 19                       Polygon zkEVM = 34
        Avalanche = 5                 Kava = 20                          Scroll = 35
        BNB = 6                       Klaytn = 21                        ShimmerEVM = 36
        Base = 7                      Linea = 22                         Telos = 37
        Canto = 8                     Loot = 23                          TomoChain = 38 
        Celo = 9                      Manta = 24                         Tenet = 39
        Conflux = 10                  Mantle = 25                        XPLA = 40
        CoreDAO = 11                  Meter = 26                         Zora = 41  
        DFK = 12                      Metis = 27                         opBNB = 42
        Ethereum = 13                 Moonbeam = 28                      zkSync = 43
        Fantom = 14                   Moonriver = 29                     Beam = 44
        Fuse = 15                     OKX = 30                           inEVM = 45
                                                                         Rarible = 46
    
    Все настройки показаны на примерах, похожие по названию настройки - работают аналогично
    
    STG_STAKE_CONFIG | [(Минимум, максимум месяцев для лока), (минимальная, максимальная сумма для лока)].
                        Софт застейкает STG в сети с большим балансом STG из STARGATE_CHAINS.
    
    STARGATE_CHAINS | Выберите чейны, между которыми будут производиться бриджи
    STARGATE_TOKENS | Выберите монеты, между которыми будут производиться свапы. Доступны: ETH, USDT, USDC, USDV, STG. 
    STARGATE_DUST_CONFIG |  Пример: (['USDV', 'USDV'], [31, 6]). Софт отправит 0.000000(1-3)% от баланса токена в сети с
                            наибольшим балансом. Применяется только к модулю bridge_stargate_dust
    
        Софт сам определит, где сейчас находиться баланс и сделает бридж по указанной логике в вышеуказанных настройках    
        
        Токены указывать в таком же порядке, как и чейны. Условно STARGATE_CHAINS = [5, 6] и
        STARGATE_TOKENS = ['USDC', 'USDT'] будет означать, что для чейна №5 будет USDC, а для №6 USDT
        Свапы для ETH производятся на значение из AMOUNT_PERCENT. 
        
        Для Stargate можно указывать любое количество сетей, софт будет делать бриджи в рандомную сеть из списка. 
               
        1) Круговой бридж с заходом из сети. Указав STARGATE_CHAINS = [1, (7, 22)], софт сделает бридж 
        из сети '1' в левую из внутреннего списка '7', далее будут бриджи между сетями из внутреннего списка, для 
        активации этого режима нужно запустить модуль один раз и указать нужное количество бриджей L0_BRIDGE_COUNT.
        Последний бридж будет в сеть '1'.
        
        2) Режим касания каждой сети. Указав STARGATE_CHAINS = [1, 7, 22] и L0_BRIDGE_COUNT равное количеству
        указанных сетей в STARGATE_CHAINS и запустив модуль 1 раз, софт попытается сделать бридж из каждой указанной
        сети. При указании L0_BRIDGE_COUNT > STARGATE_CHAINS, после попыток бриджа из каждой сети, софт будет выбирать
        рандомную сеть
        
        3) Режим строгого маршрута. Указав STARGATE_CHAINS = (1, 7, 22) и L0_BRIDGE_COUNT равное количеству
        указанных сетей в STARGATE_CHAINS и запустив модуль 1 раз, софт будет делать бриджи по очереди из каждой
        указанной сети (i) в следующую (i + 1). L0_BRIDGE_COUNT должно быть строго равно длине STARGATE_CHAINS - 1 
        
        Доступны 3-х и 2-х плечевые бриджи для CoreDAO.
        Бридж из сети первой по порядку сети в COREDAO_CHAINS, далее в CoreDAO, далее в третью сеть из COREDAO_CHAINS,
        если L0_BRIDGE_COUNT > 3, то софт будет делать по кругу этот порядок бриджей (1 - 2 - 3, а потом 3 - 2 - 1)
        
        2-х плечевые бриджи работают как обычный круговой прогон (1 - 2, 2 - 1).
        
    L0_BRIDGE_COUNT | Количество бриджей для одного запуска bridge_stargate или bridge_coredao
    L0_SEARCH_DATA | Настройка для поиска балансов во время прогона объемов. 0 - STARGATE_CHAINS, 1 - COREDAO_CHAINS  
    
    SRC_CHAIN_L2PASS = [27, 29] | Одна из сетей будет выбрана (REFUEL/BRIDGE NFT(включая Wormhole на Merkly))        

    DST_CHAIN_L2PASS_REFUEL = {
        1: (0.0016, 0.002), # Chain ID: (минимум, максимум) в нативном токене входящей сети**
        2: (0.0002, 0.0005) 
    } 
    
    WORMHOLE_TOKENS_AMOUNT | Количество токенов для минта и бриджа через Wormhole

    SRC_CHAIN_L2TELEGRAPH | Исходящая сеть для L2Telegraph
    DST_CHAIN_L2TELEGRAPH | Входящая сеть для L2Telegraph 
    
    L2PASS_ATTACK_REFUEL | Указываете в списках вариант refuel (исходящая сеть, входящая сеть, мин. сумму к refuel).     
    L2PASS_ATTACK_NFT    | Указываете в списках вариант бриджа NFT (исходящая сеть, входящая сеть). 
                    
    SHUFFLE_ATTACK | Если стоит True, то софт перемешает маршрут атаки 
    WAIT_FOR_RECEIPT | Если стоит True, то софт будет ждать получения средств во входящей сети, перед запуском модуля
                        следующего модуля
    
    L2PASS_ATTACK_REFUEL = [
        ([43, 3, 0.0001], None),  # Пример использования None для атаки: (данные для атаки, None).
    ]                               Если будет выбран None, то модуль будет пропущен 
                                    Применяется для всех модулей.
                                     
    L2PASS_ATTACK_REFUEL = [
        [43, [1, 2, 3], 0.0001],  # Пример использования случайной атаки: (исходящая сеть, список входящих сетей, сумма)
    ]                               Если будет указан список сетей, то модуль выберет одну сеть из списка.
                                    Применяется для всех модулей.
    
    L2PASS_GAS_STATION_DATA | Gas Station на L2Pass https://l2pass.com/gas-station. 
                              Указываете в списках сеть и сумму к refuel.

    Сумму нужно указывать в нативном токене входящей сети. Указывайте на 10% меньше от лимита, указанного на сайте,
    во избежания ошибок работы технологии LayerZero. Смотреть лимиты можно здесь: 
            1) L2Pass - https://l2pass.com/refuel  
            2) Merkly - https://minter.merkly.com/gas  
            3) Whale  - https://whale-app.com/refuel
            4) Zerius - https://zerius.io/refuel
            
"""
WAIT_FOR_RECEIPT = True     # Если True, будет ждать получения средств во входящей сети перед запуском очередного модуля
ALL_DST_CHAINS = False       # Если True, то модули refuel и bridge попытаются сделать транзакцию в каждую входящую сеть
L0_SEARCH_DATA = 0          # Поиск балансов в сетях. 0 - STARGATE_CHAINS, 1 - COREDAO_CHAINS

'--------------------------------------------------Stargate / CoreDAO--------------------------------------------------'

STG_STAKE_CONFIG = [(2, 3), (1, 5)]
STARGATE_DUST_CONFIG = (['USDV', 'USDV'], [31, 6])

STARGATE_CHAINS = [5, 7]
STARGATE_TOKENS = ['USDC', 'USDC']

COREDAO_CHAINS = [5, 11, 33]
COREDAO_TOKENS = ['USDC', 'USDC', 'USDC']

L0_BRIDGE_COUNT = 1

'--------------------------------------------------------L2Pass--------------------------------------------------------'

SRC_CHAIN_L2PASS = [6]          # Исходящая сеть для L2Pass
DST_CHAIN_L2PASS_NFT = [20]       # Входящая сеть для L2Pass Mint NFT
DST_CHAIN_L2PASS_REFUEL = {
    20: (0.6, 0.61),        # Chain ID: (минимум, максимум) в нативном токене входящей сети (кол-во)
}

'--------------------------------------------------------Merkly--------------------------------------------------------'

SRC_CHAIN_MERKLY = [35]         # Исходящая сеть для Merkly
DST_CHAIN_MERKLY_NFT = [43]     # Входящая сеть для Merkly Mint NFT
DST_CHAIN_MERKLY_REFUEL = {
     3: (0.000001, 0.00002),        # Chain ID: (минимум, максимум) в нативном токене входящей сети (кол-во)
     20: (0.000001, 0.00002),        # Chain ID: (минимум, максимум) в нативном токене входящей сети (кол-во)
}

'--------------------------------------------------------Whale---------------------------------------------------------'

SRC_CHAIN_WHALE = [35]          # Исходящая сеть для Whale
DST_CHAIN_WHALE_NFT = [7]     # Входящая сеть для Whale Mint NFT
DST_CHAIN_WHALE_REFUEL = {
    42: (0.0005, 0.0005),        # Chain ID: (минимум, максимум) в нативном токене входящей сети (кол-во)
}

'-------------------------------------------------------Zerius---------------------------------------------------------'

SRC_CHAIN_ZERIUS = [35]          # Исходящая сеть для Zerius
DST_CHAIN_ZERIUS_NFT = [7]      # Входящая сеть для Zerius Mint NFT
DST_CHAIN_ZERIUS_REFUEL = {
    1: (0.0001, 0.0002),        # Chain ID: (минимум, максимум) в нативном токене входящей сети (кол-во)
}

'-------------------------------------------------------Bungee---------------------------------------------------------'

SRC_CHAIN_BUNGEE = [43]          # Исходящая сеть для Bungee
DST_CHAIN_BUNGEE_REFUEL = {
    5: (0.0003, 0.00031),  # Chain ID: (минимум, максимум) в нативном токене исходящей сети (кол-во)
}

'---------------------------------------------------Merkly Wormhole----------------------------------------------------'

SRC_CHAIN_MERKLY_WORMHOLE = [9]   # Исходящая сеть для Merkly Wormhole
DST_CHAIN_MERKLY_WORMHOLE = [21, 14]  # Входящая сеть для Merkly Wormhole
WORMHOLE_TOKENS_AMOUNT = (1, 1)   # Кол-во токенов для минта и бриджа на Merkly через Wormhole

'---------------------------------------------------Merkly Polyhedra---------------------------------------------------'

SRC_CHAIN_MERKLY_POLYHEDRA = [9]   # Исходящая сеть для Merkly Polyhedra
DST_CHAIN_MERKLY_POLYHEDRA = [28]   # Входящая сеть для Merkly Polyhedra
DST_CHAIN_MERKLY_POLYHEDRA_REFUEL = {
     28: (0.000001, 0.00002),        # Chain ID: (минимум, максимум) в нативном токене входящей сети (кол-во)
}

'---------------------------------------------------Merkly Hyperlane---------------------------------------------------'

SRC_CHAIN_MERKLY_HYPERLANE = [9]   # Исходящая сеть для Merkly Hyperlane
DST_CHAIN_MERKLY_HYPERLANE = [17, 28]   # Входящая сеть для Merkly Hyperlane
HYPERLANE_TOKENS_AMOUNT = (1, 1)   # Кол-во токенов для минта и бриджа на Merkly через Hyperlane

'------------------------------------------------------L2Telegraph-----------------------------------------------------'

SRC_CHAIN_L2TELEGRAPH = [33]    # Исходящая сеть для L2Telegraph.
DST_CHAIN_L2TELEGRAPH = [2]     # Входящая сеть для L2Telegraph.

'------------------------------------------------LAYERZERO REFUEL ATTACKS----------------------------------------------'

SHUFFLE_ATTACK = True      # Если True, то перемешает маршрут для Refuel атаки перед стартом
SHUFFLE_NFT_ATTACK = True  # Если True, то перемешает маршрут для NFT атаки перед стартом

L2PASS_ATTACK_REFUEL = [
    [43, [1, 2, 3], 0.0001],  # Пример разных входящих сетей
    [33, 5, 0.0001],
]

MERKLY_ATTACK_REFUEL = [
    ([43, 3, 0.0001], None),  # Пример возможности исключить модуль из маршрута
    [33, 5, 0.0001],
]

WHALE_ATTACK_REFUEL = [
    [28, 17, 0.00001],
    [29, 20, 0.00001],
]

ZERIUS_ATTACK_REFUEL = [
    [33, 5, 0.0001],
]

'-------------------------------------------------LAYERZERO NFT ATTACKS------------------------------------------------'

L2PASS_ATTACK_NFT = [
    [17, 18],
]

MERKLY_ATTACK_NFT = [
    [43, 3],
]

WHALE_ATTACK_NFT = [
    [17, 18],
]

ZERIUS_ATTACK_NFT = [
    [43, 3],
]

'-------------------------------------------------LAYERZERO GAS STATION------------------------------------------------'

L2PASS_GAS_STATION_ID_FROM = [33]
L2PASS_GAS_STATION_DATA = [
    ([35, 0.0000001], None),   # Пример возможности исключить модуль из маршрута
    [[34,36, 35], 0.0000001],  # Пример разных входящих сетей
    [34, 0.0000001],
]

"""
-----------------------------------------------------OTHER SETTINGS-----------------------------------------------------

    ZKSTARS_NFT_CONTRACTS | Укажите какие NFT ID будут участвовать в минте. Все что в скобках, будут использованы
    MINTFUN_CONTRACTS | Список контрактов для минта в выбранной сети (GLOBAL NETWORK)
    GRAPEGRAW_TICKETS_AMOUNT | Количество билетов для покупки в одной транзакции на сайте https://grapedraw.com/
    ZKSYNC_PAYMASTER_TOKEN | Укажите каким токеном вы будете совершать оплату за газ при использовании paymaster 
    CUSTOM_SWAP_DATA | ('токен для обмена', 'токен для получения', (сумма от и до), сеть запуска(см. OMNI-CHAIN))
    
"""
CUSTOM_SWAP_DATA = ('USDC.e', 'USDC', ('100', '100'), 31)

ZKSTARS_NFT_CONTRACTS = (1, 2, 3, 4)  # при 0 заминтит все NFT в случайном порядке

ZKSYNC_PAYMASTER_TOKEN = 0  # 0 - USDT, 1 - USDC

GRAPEDRAW_TICKETS_AMOUNT = 1

MINTFUN_CONTRACTS = [
    '0xEb3805E0776180A783aD7f637e08172D40240311',
]

"""
-------------------------------------------------GOOGLE-ROUTES CONTROL--------------------------------------------------
    Технология сохранения прогресса для каждого аккаунта с помощью Google Spreadsheets 
    При каждом запуске, софт будет брать информацию из Google таблицы и настроек снизу, для генерации уникального
     маршрута под каждый аккаунт в таблице.  
    ⚠️Количество аккаунтов и их расположение должно быть строго одинаковым для вашего Excel и Google Spreadsheets⚠️
                                                         
    DEPOSIT_CONFIG | Включает в маршрут для каждого аккаунта модули, со значениями '1'
                     'okx_withdraw' всегда будет первой
                     Бриджи всегда после 'okx_withdraw'
                     'okx_deposit' и 'okx_collect_from_sub' всегда последние
    
"""
DMAIL_COUNT = (0, 0)          # (минимум, максимум) дополнительных транзакций для Dmail
TRANSFER_COUNT = (0, 0)       # (минимум, максимум) дополнительных транзакций для трансферов
COLLATERAL_COUNT = (0, 0)     # (минимум, максимум) дополнительных транзакций для вкл/выкл страхования
WRAPS_COUNT = (0, 0)          # (минимум, максимум) транзакций через модуль wrap_abuser

MODULES_COUNT = (1, 1)         # (минимум, максимум) неотработанных модулей из Google таблицы
ALL_MODULES_TO_RUN = False     # True или False | Включает все неотработанные модули в маршрут
WITHDRAW_LP = False            # True или False | Включает в маршрут все модули для вывода ликвидности из DEX
WITHDRAW_LANDING = False       # True или False | Включает в маршрут все модули для вывода ликвидности из лендингов
HELP_NEW_MODULE = False        # True или False | Добавляет случайный модуль при неудачном выполнении модуля из маршрута
EXCLUDED_MODULES = ['swap_openocean']  # Исключает выбранные модули из маршрута. Список в Classic-Routes
INCLUDED_MODULES = []          # Включает выбранные модули в маршрут. Список в Classic-Routes

HELPERS_CONFIG = {
    'okx_withdraw'                        : 0,  # смотри CEX CONTROL
    'bingx_withdraw'                      : 0,  # смотри CEX CONTROL
    'binance_withdraw'                    : 0,  # смотри CEX CONTROL
    'bitget_withdraw'                     : 0,  # смотри CEX CONTROL
    'collector_eth'                       : 0,  # сбор всех токенов в ETH внутри сети GLOBAL_NETWORK
    'make_balance_to_average'             : 0,  # уравнивает ваши балансы на аккаунтах (см. инструкцию к софту)
    'bridge_across'                       : 0,  # смотри BRIDGE CONTROL
    'bridge_bungee'                       : 0,  # смотри BRIDGE CONTROL
    'bridge_layerswap'                    : 0,  # смотри BRIDGE CONTROL
    'bridge_owlto'                        : 0,  # смотри BRIDGE CONTROL
    'bridge_orbiter'                      : 0,  # смотри BRIDGE CONTROL
    'bridge_relay'                        : 0,  # смотри BRIDGE CONTROL
    'bridge_rhino'                        : 0,  # смотри BRIDGE CONTROL
    'bridge_native'                       : 0,  # смотри BRIDGE CONTROL (кол-во из NATIVE_DEPOSIT_AMOUNT)
    'okx_deposit'                         : 0,  # ввод средств на биржу
    'bingx_deposit'                       : 0,  # ввод средств на биржу
    'binance_deposit'                     : 0,  # ввод средств на биржу
    'bitget_deposit'                      : 0,  # ввод средств на биржу
}

"""
--------------------------------------------CLASSIC-ROUTES CONTROL------------------------------------------------------

---------------------------------------------------HELPERS--------------------------------------------------------------        

    okx_withdraw                     # смотри CEX CONTROL
    bingx_withdraw                   # смотри CEX CONTROL
    binance_withdraw                 # смотри CEX CONTROL
    bitget_withdraw                  # смотри CEX CONTROL
    
    bridge_across                    # смотри BRIDGE CONTROL
    bridge_bungee                    # смотри BRIDGE CONTROL
    bridge_layerswap                 # смотри BRIDGE CONTROL
    bridge_nitro                     # смотри BRIDGE CONTROL
    bridge_owlto                     # смотри BRIDGE CONTROL
    bridge_orbiter                   # смотри BRIDGE CONTROL
    bridge_relay                     # смотри BRIDGE CONTROL
    bridge_rhino                     # смотри BRIDGE CONTROL
    bridge_native                    # смотри BRIDGE CONTROL (кол-во из NATIVE_DEPOSIT_AMOUNT) 
    
    okx_deposit                      # ввод средств на биржу + сбор средств на субАккаунтов на основной счет
    bingx_deposit                    # ввод средств на биржу + сбор средств на субАккаунтов на основной счет
    binance_deposit                  # ввод средств на биржу + сбор средств на субАккаунтов на основной счет
    bitget_deposit                   # ввод средств на биржу + сбор средств на субАккаунтов на основной счет
        
    custom_swap                      # производит свап по настройке CUSTOM_SWAP_DATA
    collector_eth                    # сбор всех токенов на аккаунте в ETH
    make_balance_to_average          # уравнивает ваши балансы на аккаунтах (см. CEX_BALANCE_WANTED) 
    
    claim_rewards_bungee             # клейм наград за бриджи через Socket на сайте https://www.socketscan.io/rewards
    
--------------------------------------------------OMNI-CHAIN------------------------------------------------------------            
    
    bridge_l2pass                    # bridge последней NFT on L2Pass
    bridge_merkly                    # bridge последней NFT on Merkly
    bridge_whale                     # bridge последней NFT on Whale
    bridge_zerius                    # bridge последней NFT on Zerius
    
    refuel_l2pass                    # смотри OMNI-CHAIN CONTROL
    refuel_merkly                    # смотри OMNI-CHAIN CONTROL
    refuel_whale                     # смотри OMNI-CHAIN CONTROL
    refuel_zerius                    # смотри OMNI-CHAIN CONTROL
    refuel_bungee                    # смотри OMNI-CHAIN CONTROL
    
    smart_stake_stg                  # стейк на Stargate. STG_STAKE_CONFIG. См. OMNI-CHAIN CONTROLE
    bridge_stargate                  # бриджи на Stargate. STARGATE_CHAINS, STARGATE_TOKENS. См. OMNI-CHAIN CONTROLE
    bridge_coredao                   # бриджи на CoreDAO. COREDAO_CHAINS, COREDAO_TOKENS. См. OMNI-CHAIN CONTROLE
    smart_random_approve             # рандомный апрув для сети с наибольшим балансом из L0_SEARCH_DATA 
    
    mint_and_bridge_l2telegraph      # mint и bridge NFT через L2Telegraph. См. OMNI-CHAIN CONTROLE
    send_message_l2telegraph         # смотри OMNI-CHAIN CONTROL
    
    l2pass_refuel_attack             # Refuel атака на L2Pass. Делает много рефьелов в разные сети. См. OMNI-CHAIN CONTROLE
    merkly_refuel_attack             # Refuel атака на Merkly. Делает много рефьелов в разные сети. См. OMNI-CHAIN CONTROLE
    whale_refuel_attack              # Refuel атака на Whale. Делает много рефьелов в разные сети. См. OMNI-CHAIN CONTROLE
    zerius_refuel_attack             # Refuel атака на Zerius. Делает много рефьелов в разные сети. См. OMNI-CHAIN CONTROLE
    
    l2pass_nft_attack                # NFT Bridge атака на L2Pass.
    merkly_nft_attack                # NFT Bridge атака на Merkly.
    whale_nft_attack                 # NFT Bridge атака на Whale.
    zerius_nft_attack                # NFT Bridge атака на Zerius.
    
    gas_station_l2pass               # Refuel в несколько сетей с помощью 1 транзакции. см. L2PASS_GAS_STATION_DATA     
    
--------------------------------------------------------WORMHOLE--------------------------------------------------------            

    bridge_wormhole_nft     # минт и бридж NFT на Merkly через Wormhole 
    bridge_wormhole_token   # минт и бридж токенов на Merkly через Wormhole 
    
-------------------------------------------------------POLYHEDRA--------------------------------------------------------            

    bridge_polyhedra_nft     # минт и бридж NFT на Merkly через Polyhedra 
    refuel_polyhedra         # refuel на Merkly через Polyhedra 
    
-------------------------------------------------------HYPERLANE--------------------------------------------------------            

    bridge_hyperlane_nft     # минт и бридж NFT на Merkly через Hyperlane 
    bridge_hyperlane_token   # минт и бридж токенов на Merkly через Hyperlane 
    
---------------------------------------------------------ZKSYNC---------------------------------------------------------        

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
    swap_syncswap_paymaster                   
    swap_velocore                    
    swap_xyfinance                   
    swap_vesync                      
    swap_woofi                       
    swap_zkswap                 
    check_in_owlto                   # checkIn на сайте https://owlto.finance/confirm
    wrap_eth                         # wrap/unwrap ETH через офф. контракт токена WETH. (кол-во из LIQUIDITY_AMOUNT)
    grapedraw_bid                    # создание ставки на GrapeDraw https://grapedraw.com. см. GRAPEDRAW_TICKETS_AMOUNT 
    vote_rubyscore                   # голосование на RubyScore https://rubyscore.io 
    create_omnisea                   # создание новой NFT коллекции. Все параметры будут рандомными
    create_safe                      # создает сейф в сети GLOBAL_NETWORK
    mint_domain_ens                  # 0.003 ETH domain
    mint_domain_zns                  # 0.003 ETH domain
    mint_mailzero                    # mint бесплатной NFT на MailZero. Плата только за газ.
    mint_tevaera                     # mint 2 NFT on Tevaera. Price: 0.0003 ETH
    mint_hypercomic                  # mint NFT за выполнение квестов на https://zk24.hypercomic.io/
    mint_zkstars                     # mint NFT на сайте https://zkstars.io. Price: 0.0001 ETH
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
    
---------------------------------------------------------BLAST----------------------------------------------------------  

    swap_bebop
    swap_thruster
    swap_bladeswap
    swap_ambient
    check_in_owlto
    deposit_abracadabra
    deposit_zerolend
    deposit_usdb_zerolend
    deposit_abracadabra_with_lock
    withdraw_abracadabra
    
------------------------------------------------------Polygon zkEVM-----------------------------------------------------  
    
    swap_quickswap
    swap_pancake
    swap_woofi
    swap_rango
    swap_openocean
    swap_xyfinance
    
----------------------------------------------------------BASE----------------------------------------------------------        

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
    deposit_seamless
    withdraw_seamless
    deposit_usdbc_seamless
    withdraw_usdbc_seamless
    deposit_moonwell
    withdraw_moonwell
    enable_collateral_moonwell
    disable_collateral_moonwell
    enable_collateral_seamless
    disable_collateral_seamless
    create_safe
    mint_mintfun
    mint_zkstars
    deploy_contract
    vote_rubyscore
    random_approve
    transfer_eth                     
    transfer_eth_to_myself
    wrap_abuser                      
    send_message_dmail
    withdraw_native_bridge

----------------------------------------------------------LINEA---------------------------------------------------------        

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
    check_in_owlto
    mint_zkstars
    deploy_contract
    vote_rubyscore
    random_approve
    transfer_eth                     
    transfer_eth_to_myself
    wrap_abuser                     
    send_message_dmail
    withdraw_native_bridge          

---------------------------------------------------------SCROLL---------------------------------------------------------        
    
    add_liquidity_syncswap           # USDC/WETH LP на LIQUIDITY_AMOUNT
    swap_rango
    swap_ambient
    swap_zebra
    swap_sushiswap
    swap_skydrome
    swap_syncswap
    swap_spacefi
    swap_izumi
    swap_openocean
    swap_xyfinance
    check_in_owlto
    deposit_layerbank
    withdraw_layerbank
    deposit_rocketsam
    withdraw_rocketsam
    create_omnisea
    mint_zkstars
    deploy_contract
    vote_rubyscore
    random_approve
    transfer_eth                     
    transfer_eth_to_myself   
    send_message_dmail
    wrap_abuser                     
    withdraw_native_bridge
    
----------------------------------------------------------ZORA----------------------------------------------------------        
    
    bridge_zora
    mint_mintfun
    mint_zkstars
    deposit_rocketsam
    transfer_eth                     
    transfer_eth_to_myself

----------------------------------------------------------NOVA----------------------------------------------------------        
    
    swap_sushiswap
    deposit_rocketsam                          
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

CLASSIC_WITHDRAW_DEPENDENCIES = False  # при True после каждого модуля на добавление ликвы в лендинг, будет ее выводить

CLASSIC_ROUTES_MODULES_USING = [
    ['okx_withdraw'],
    ['bridge_layerswap', 'bridge_native'],
    ['swap_mute', 'swap_izumi', 'mint_domain_ens', None],
]
