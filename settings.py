"""
-------------------------------------------------OKX WITHDRAW-----------------------------------------------------------
    Выберите сети для вывода и ввода с OKX. Софт работает только с токеном ETH. Не забудьте вставить API ключи снизу.

    1 - ETH-ERC20
    2 - ETH-Arbitrum One
    3 - ETH-zkSync Lite
    4 - ETH-Optimism
    5 - ETH-Starknet
    6 - ETH-zkSync Era
    7 - ETH-Linea

    OKX_BRIDGE_NEED | Если включен(стоит True), то перед депозитом на биржу софт сделает бридж в сеть из который
                        планируется пополнять OKX. Если сеть для пополнения OKX есть в списке сверху, то ставьте False
    OKX_DEPOSIT_AMOUNT | Определяет % от баланса основной сети (GLOBAL_NETWORK) для выполнения бриджа в сеть
                            пополнения OKX (OKX_DEPOSIT_NETWORK)
    OKX_DEPOSIT_AMOUNT = 90 | % of MAX TOKEN BALANCE. Will withdraw this amount from the largest token balance in zkSync
    OKX_BRIDGE_MODE = [1, 2, 3] | 1 - Rhino.fi, 2 - Orbiter, 3 - LayerSwap. Выберите мосты для бриджа в сеть, из которой
                                    планируется пополнять OKX. Софт выберет один из списка

------------------------------------------------------------------------------------------------------------------------
"""
OKX_WITHDRAW_NETWORK = 5              # Сеть вывода из OKX
OKX_WITHDRAW_AMOUNT = (0.001, 0.0015)  # (минимальная, максимальная) сумма в ETH для вывода

OKX_BRIDGE_NEED = False                # True или False | Включает бридж в выбранную сеть (OKX_DEPOSIT_NETWORK)
OKX_BRIDGE_MODE = [1]                 # Мосты для бриджа в сеть пополнения OKX
OKX_BRIDGE_AMOUNT = 90               # % от баланса основной сети (GLOBAL_NETWORK)
OKX_DEPOSIT_NETWORK = 5               # Сеть из которой планируется пополнение OKX
OKX_DEPOSIT_AMOUNT = (0.001, 0.001)   # (минимальная, максимальная) сумма в ETH на пополнение OKX

"""
--------------------------------------------------Native Bridge---------------------------------------------------------
    Официальные мосты для бриджей из ERC20. Укажите сумму для бриджа/вывода в ETH. 

    Можно указать минимальную/максимальную сумму или минимальный/максимальный % от баланса
    
    Количество - (0.01, 0.02)
    Процент    - ("10", "20") ⚠️ Значения в скобках
"""
NATIVE_DEPOSIT_AMOUNT = (0.01, 0.02)    # (минимум, максимум) ETH или %
NATIVE_WITHDRAW_AMOUNT = (0.001, 0.02)  # (минимум, максимум) ETH или %

"""
------------------------------------------------LayerSwap Bridge--------------------------------------------------------
    Проверьте руками, работает ли сеть на сайте. (Софт сам проверит, но зачем его напрягать?)
    Софт работает только с токеном ETH. Не забудьте вставить API ключи снизу.
       
    Arbitrum = 1            Optimism = 7
    Arbitrum Nova = 2       Scroll = 8  
    Base = 3                Starknet = 9   
    Linea = 4               Polygon ZKEVM = 10    
    Manta = 5               zkSync Era = 11  
    Polygon = 6             Zora = 12
                            zkSync Lite = 13
    
    LAYERSWAP_CHAIN_ID_FROM(TO) = [2, 4, 16] | Одна из сетей будет выбрана
    LAYERSWAP_REFUEL | Добавляет немного нативного токена в сеть пополнения
"""
LAYERSWAP_CHAIN_ID_FROM = [9]   # Исходящая сеть
LAYERSWAP_CHAIN_ID_TO = [1]        # Входящая сеть
LAYERSWAP_AMOUNT = (0.003, 0.004)   # (минимум, максимум) ETH или %
LAYERSWAP_REFUEL = False            # True or False

"""
------------------------------------------------Orbiter Bridge----------------------------------------------------------
    Проверьте руками, работает ли сеть на сайте. (Софт сам проверит, но зачем его напрягать?)
    Софт работает только с токеном ETH.

    Arbitrum = 1            Optimism = 7
    Arbitrum Nova = 2       Scroll = 8  
    Base = 3                Starknet = 9   
    Linea = 4               Polygon ZKEVM = 10    
    Manta = 5               zkSync Era = 11  
    Polygon = 6             Zora = 12
                            zkSync Lite = 13

    ORBITER_CHAIN_ID_FROM(TO) = [2, 4, 11] | Одна из сетей будет выбрана
"""
ORBITER_CHAIN_ID_FROM = [9]          # Исходящая сеть
ORBITER_CHAIN_ID_TO = [1]            # Входящая сеть
ORBITER_AMOUNT = (0.001, 0.001)      # (минимум, максимум) ETH или %

"""
-------------------------------------------------Rhino Bridge-----------------------------------------------------------
    Проверьте руками, работает ли сеть на сайте. (Софт сам проверит, но зачем его напрягать?)
    Софт работает только с токеном ETH.
    
    Arbitrum = 1           *Polygon = 6
    Arbitrum Nova = 2       Optimism = 7
    Base = 3                Scroll = 8  
    Linea = 4               Starknet = 9       
    Manta = 5               Polygon ZKEVM = 10         
                            zkSync Era = 11   
                            
    * - Не работает для RHINO_CHAIN_ID_FROM                
    RHINO_CHAIN_ID_FROM(TO) = [2, 3, 10] | Одна из сетей будет выбрана
"""
RHINO_CHAIN_ID_FROM = [1]              # Исходящая сеть
RHINO_CHAIN_ID_TO = [11]                # Входящая сеть
RHINO_AMOUNT = (0.004, 0.005)          # (минимум, максимум) ETH или %

"""
---------------------------------------------OMNI-CHAIN CONTROL---------------------------------------------------------
    Проверьте руками, работают ли сети на сайте. (Софт сам проверит, но зачем его напрягать?)

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

    SOURCE_CHAIN_ZERIUS = [27, 29] | Одна из сетей будет выбрана (BRIDGE NFT)
    SOURCE_CHAIN_MERKLY = [27, 29] | Одна из сетей будет выбрана (REFUEL)
    DESTINATION_MERKLY_AMOUNT = {
        1: (0.0016, 0.002), # Chain ID: (минимум, максимум) в нативном токене входящей сети**
        2: (0.0002, 0.0005) 
    } 
    
    *   - Могут быть использованы как исходящие сеть для Zerius, Merkly
    (B) - Поддерживаемые входящие сети в Bungee
    **  - Сумму для Merkly нужно подавать в нативном токене входящей сети. И указывайте на 5-10% меньше от лимита,
            во избежания ошибок работы софта. Смотреть лимиты можно здесь https://minter.merkly.com/gas  
"""
SOURCE_CHAIN_ZERIUS = [27, 29]  # Исходящая сеть для Zerius
DESTINATION_ZERIUS = [1, 4, 8]  # Входящая сеть для Zerius

SOURCE_CHAIN_MERKLY = [1]       # Исходящая сеть для Merkly
DESTINATION_MERKLY_DATA = {
    27: (0.01, 0.01),  # Chain ID: (минимум, максимум) в нативном токене входящей сети**
    28: (0.04, 0.05)
}

DESTINATION_BUNGEE_DATA = {
    3:  (0.001, 0.0015),  # Chain ID: (min amount, max amount) in ETH
    22: (0.001, 0.0015)   # Chain ID: (min amount, max amount) in ETH
}

DESTINATION_L2TELEGRAPH = [22]  # Входящая сеть для L2Telegraph. Можно указать несколько ([1, 2]) и будет выбрана одна.

"""
----------------------------------------------AMOUNT CONTROL------------------------------------------------------------
    Здесь вы определяете количество или % токенов для обменов, добавления ликвидности, депозитов и трансферов
    Софт берет % только для ETH, остальные токены берутся на 100% от баланса
    
    Можно указать минимальную/максимальную сумму или минимальный/максимальный % от баланса
    
    Количество - (0.01, 0.02)
    Процент    - ("10", "20") ⚠️ Значения в скобках
    
    MIN_BALANCE | Минимальный баланс для аккаунта. При меньшем балансе, будет ошибка: (Insufficient balance on account!)
"""
AMOUNT_PERCENT = (50, 60)             # Применяется для обменов
LANDING_AMOUNT = (0.0005, 0.001)      # Применяется для депозитов на лендинги и wrap ETH
DEX_LP_AMOUNT = (0.0005, 0.001)       # Применяется для добавления ликвидности
TRANSFER_AMOUNT = (0.00001, 0.00005)  # Применяется для трансферов
MIN_BALANCE = 0.001                   # Количество ETH на аккаунте

"""
------------------------------------------------GENERAL SETTINGS--------------------------------------------------------
    GLOBAL_NETWORK | Блокчейн для основного взаимодействия ⚠️
    
    Arbitrum = 1            Polygon = 6
    Arbitrum Nova = 2       Optimism = 7
    Base = 3                Scroll = 8  
    Linea = 4               Starknet = 9
    Manta = 5               Polygon ZKEVM = 10     
                            zkSync Era = 11     
    
    WALLETS_TO_WORK = 0 | Софт будет брать кошельки из таблице по правилам, описаным снизу
    0       = все кошельки подряд
    3       = только кошелек №3 
    4, 20   = кошелек №4 и №20
    [5, 25] = кошельки с №5 по №25
    
    ACCOUNTS_IN_STREAM      | Количество кошельков в потоке на выполнение. Если всего 100 кошельков, а указать 10,
                                то софт сделает 10 подходов по 10 кошельков
    CONTROL_TIMES_FOR_SLEEP | Количество проверок, после которого для всех аккаунтов будет включен рандомный сон в 
                                моменте, когда газ опуститься до MAXIMUM_GWEI и аккаунты продолжат работать
                                
    EXCEL_PASSWORD          | Включает запрос пароля при входе в софт. Сначала установите пароль в таблице
    EXCEL_PAGE_NAME         | Название листа в таблице. Пример: 'Starknet' 
    GOOGLE_SHEET_URL        | Ссылка на вашу Google таблицу с прогрессом аккаунтов
    GOOGLE_SHEET_PAGE_NAME  | Аналогично EXCEL_PAGE_NAME   
"""
GLOBAL_NETWORK = 9              # 16.11.2023 поддерживается только zkSync и Starknet. Следите за новостями.
SOFTWARE_MODE = 1               # 0 - последовательный запуск / 1 - параллельный запуск
ACCOUNTS_IN_STREAM = 1        # Только для SOFTWARE_MODE = 1 (параллельный запуск)
WALLETS_TO_WORK = 1             # 0 / 3 / 3, 20 / [3, 20]
SAVE_PROGRESS = False           # True или False | Включает сохранение прогресса аккаунта для Classic-routes
TELEGRAM_NOTIFICATIONS = True   # True или False | Включает уведомления в Telegram


'------------------------------------------------SLEEP CONTROL---------------------------------------------------------'
SLEEP_MODE = False              # True или False | Включает сон после каждого модуля и аккаунта
SLEEP_TIME = (25, 30)           # (минимум, максимум) секунд | Время сна между модулями.
SLEEP_TIME_STREAM = (1, 2)    # (минимум, максимум) секунд | Время сна между аккаунтами.

'-------------------------------------------------GAS CONTROL----------------------------------------------------------'
GAS_CONTROL = False             # True или False | Включает контроль газа
MAXIMUM_GWEI = 40               # Максимальный GWEI для работы софта
SLEEP_TIME_GAS = 10             # Время очередной проверки газа
CONTROL_TIMES_FOR_SLEEP = 3     # Количество проверок
GAS_MULTIPLIER = 1.1            # Множитель газа для транзакций


'------------------------------------------------RETRY CONTROL---------------------------------------------------------'
MAXIMUM_RETRY = 0               # Количество повторений при ошибках
SLEEP_TIME_RETRY = 5            # Время сна после очередного повторения


'------------------------------------------------PROXY CONTROL---------------------------------------------------------'
USE_PROXY = False               # True или False | Включает использование прокси
MOBILE_PROXY = False            # True или False | Включает использование мобильных прокси. USE_PROXY должен быть True
MOBILE_PROXY_URL_CHANGER = ['',
                            '',
                            '']  # ['link1', 'link2'..] | Ссылки для смены IP


'-----------------------------------------------SLIPPAGE CONTROL-------------------------------------------------------'
SLIPPAGE = 1                # 0.54321 = 0.54321%, 1 = 1% | Slippage, на сколько % вы готовы получить меньше
PRICE_IMPACT = 3            # 0.54321 = 0.54321%, 1 = 1% | Максимальное влияние на цену при обменах токенов


'-----------------------------------------------APPROVE CONTROL--------------------------------------------------------'
UNLIMITED_APPROVE = False       # True или False Включает безлимитный Approve для контракта


'------------------------------------------------SECURE DATA-----------------------------------------------------------'
# OKX API KEYS https://www.okx.com/ru/account/my-api
OKX_API_KEY = ""
OKX_API_SECRET = ""
OKX_API_PASSPHRAS = ""

# EXCEL AND GOOGLE INFO
EXCEL_PASSWORD = False
EXCEL_PAGE_NAME = "Starknet"
GOOGLE_SHEET_URL = ""
GOOGLE_SHEET_PAGE_NAME = "Starknet"

# TELEGRAM DATA
TG_TOKEN = ""  # https://t.me/BotFather
TG_ID = ""  # https://t.me/getmyid_bot

# INCH API KEY https://portal.1inch.dev/dashboard
ONEINCH_API_KEY = ""

# LAYERSWAP API KEY https://www.layerswap.io/dashboard
LAYERSWAP_API_KEY = ""


"""
-------------------------------------------------STARKNET SETTINGS------------------------------------------------------

    STARKSTARS_NFT_CONTRACTS | Укажите какие NFT ID будут участвовать в минте. Все что в скобках, будут использованы
    NEW_WALLET_TYPE | Определяет какой кошелек будет задеплоен, если вы решили создать новый. 0 - ArgentX | 1 - Braavos
"""

STARKSTARS_NFT_CONTRACTS = (1, 2, 3, 20)  # при (0) заминтит случайную новую NFT
NEW_WALLET_TYPE = 1

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

DMAIL_IN_ROUTES = True       # True или False | Включает Dmail в маршрут
TRANSFER_IN_ROUTES = False    # True или False | Включает трансферы в маршрут
COLLATERAL_IN_ROUTES = True  # True или False | Включает случайное вкл/выкл страховки в маршрут

DMAIL_COUNT = (1, 1)          # (минимум, максимум) дополнительных транзакций для Dmail
TRANSFER_COUNT = (1, 2)       # (минимум, максимум) дополнительных транзакций для трансферов
COLLATERAL_COUNT = (1, 2)     # (минимум, максимум) дополнительных транзакций для вкл/выкл страхования

MODULES_COUNT = (5, 6)        # (минимум, максимум) неотработанных модулей из Google таблице
ALL_MODULES_TO_RUN = False    # True или False | Включает все неотработанные модули в маршрут
WITHDRAW_LP = False           # True или False | Включает в маршрут все модули для вывода ликвидности из DEX
WITHDRAW_LANDING = False      # True или False | Включает в маршрут все модули для вывода ликвидности из лендингов
HELP_NEW_MODULE = False       # True или False | Добавляет случайный модуль при неудачном выполнении модуля из маршрута
EXCLUDED_MODULES = ['create_safe']  # Исключает выбранные модули из маршрута. Список в Classic-Routes.

DEPOSIT_CONFIG = {
    'okx_withdraw'                        : 1,  # смотри OKX настройки
    'upgrade_stark_wallet'                : 0,  # обновляет кошелек, во время маршрута
    'deploy_stark_wallet'                 : 1,  # деплоит кошелек, после вывода с OKX
    'bridge_rhino'                        : 0,  # смотри Rhino настройки
    'bridge_layerswap'                    : 0,  # смотри LayerSwap настройки
    'bridge_orbiter'                      : 0,  # смотри Orbiter настройки
    'bridge_native'                       : 0,  # смотри Native Bridge настройки
    'okx_deposit'                         : 0,  # смотри OKX настройки
    'okx_collect_from_sub'                : 0   # смотри OKX настройки
}

"""
--------------------------------------------CLASSIC-ROUTES CONTROL------------------------------------------------------

---------------------------------------------------DEPOSIT--------------------------------------------------------------        

    
    okx_withdraw                     # смотри OKX настройки
    bridge_rhino                     # смотри Rhino настройки
    bridge_layerswap                 # смотри LayerSwap настройки
    bridge_orbiter                   # смотри Orbiter настройки
    bridge_native                    # смотри Native Bridge настройки
    okx_deposit                      # ввод средств на биржу
    okx_collect_from_sub             # сбор средств на субАккаунтов на основной счет
    
----------------------------------------------------ZKSYNC--------------------------------------------------------------        

    add_liquidity_maverick           # USDC/WETH LP
    add_liquidity_mute               # USDC/WETH LP
    add_liquidity_syncswap           # USDC/WETH LP
    deposit_basilisk                 
    deposit_eralend                  
    deposit_reactorfusion            
    deposit_zerolend                 
    enable_collateral_basilisk       
    enable_collateral_eralend        
    enable_collateral_reactorfusion  
    enable_collateral_zerolend       
    swap_izumi                       
    swap_maverick                    
    swap_jediswap                    
    swap_mute                        
    swap_odos                        
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
    wrap_eth                         
    create_omnisea                   # создание новой NFT коллекции
    create_safe                      # создает сейф в сети
    mint_and_bridge_l2telegraph      # mint и bridge nft через L2Telegraph
    mint_domain_ens                  # 0.003 ETH domain
    mint_domain_zns                  # бесплатный domain
    mint_mailzero                    # mint бесплатной NFT on MainZero
    mint_tevaera                     # mint 2 NFT on Tevaera
    mint_zerius                      # mint NFT on Zerius
    bridge_zerius                    # bridge последней NFT on Zerius
    deploy_contract                  # deploy вашего контракта
    refuel_bungee                    # смотри Omni-Chain настройки
    refuel_merkly                    # смотри Omni-Chain настройки
    send_message_dmail               
    send_message_l2telegraph         # смотри Omni-Chain настройки
    transfer_eth                     
    transfer_eth_to_myself           
    withdraw_native_bridge    
                  
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
    enable_collateral_zklend
    disable_collateral_zklend
    mint_starknet_identity
    mint_starkstars
    withdraw_nostra
    withdraw_zklend
    
    Роуты для настоящих древлян (Машина - зло).
    Выберите необходимые модули для взаимодействия
    Вы можете создать любой маршрут, софт отработает строго по нему. Для каждого списка будет выбран один модуль в
    маршрут, если софт выберет None, то он пропустит данный список модулей. 
    Список модулей сверху.
    
    CLASSIC_ROUTES_MODULES_USING = [
        ['okx_withdraw'],
        ['bridge_layerswap', 'bridge_txsync', None],
        ['swap_mute', 'swap_izumi', 'mint_domain_ens'],
        ...
    ]
"""
CLASSIC_ROUTES_MODULES_USING = [
    ['disable_collateral_zerolend'],
    # ['enable_collateral_eralend', 'enable_collateral_zerolend'],
    # ['send_message_dmail'],
    # ['mint_tevaera', 'mint_and_bridge_l2telegraph'],
    # ['enable_collateral_basilisk', 'enable_collateral_eralend', None],
    # ['swap_rango', 'swap_zkswap'],
    # ['refuel_merkly', 'swap_syncswap'],
    # ['mint_domain_zns', 'mint_domain_ens'],
    # [None, 'wrap_eth', 'swap_pancake'],
    # ['swap_mute', 'swap_spacefi', 'swap_pancake'],
    # ['refuel_bungee', 'refuel_merkly'],
    # ['swap_oneinch', 'mint_domain_ens'],
    # ['mint_mailzero', 'swap_vesync'],
    # ['withdraw_txsync']
]


