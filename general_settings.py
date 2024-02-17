"""
----------------------------------------------AMOUNT CONTROL------------------------------------------------------------
    Здесь вы определяете количество или % токенов для обменов, добавления ликвидности, депозитов и трансферов
    Софт берет % только для ETH, остальные токены берутся на 100% от баланса

    Можно указать минимальную/максимальную сумму или минимальный/максимальный % от баланса

    Количество - (0.01, 0.02)
    Процент    - ("55", "60") ⚠️ Значения в скобках

    AMOUNT_PERCENT_WRAPS
    AMOUNT_PERCENT | Указывать только %, без кавычек. Можно указывать с точностью до 6 цифры (99.123456, 99.654321).
                        ⚠️Остальные настройки сумм указывать в кавычках(если хотите работать в %)⚠️
    MIN_BALANCE | Минимальный баланс для аккаунта. При меньшем балансе будет ошибка: (Insufficient balance on account!)
"""
AMOUNT_PERCENT = (55, 60)  # Применяется для обменов.
AMOUNT_PERCENT_WRAPS = (55, 60)  # Применяется для модуля wrap_abuser.
LIQUIDITY_AMOUNT = (0.001, 0.002)  # Применяется для добавления ликвидности, депозитов на лендинги и wrap ETH
TRANSFER_AMOUNT = (0.0001, 0.0002)  # Применяется для трансферов
MIN_BALANCE = 0.001  # Количество ETH на аккаунте

"""
------------------------------------------------GENERAL SETTINGS--------------------------------------------------------
    GLOBAL_NETWORK | Блокчейн для основного взаимодействия ⚠️

    Arbitrum = 1            Optimism = 7
    Arbitrum Nova = 2       Scroll = 8
    Base = 3                Starknet = 9
    Linea = 4               Polygon ZKEVM = 10
    Manta = 5               zkSync Era = 11
    Polygon = 6             Zora = 12
                            Gnosis = 20

    WALLETS_TO_WORK = 0 | Софт будет брать кошельки из таблице по правилам, описанным снизу
    0       = все кошельки подряд
    3       = только кошелек №3
    4, 20   = кошелек №4 и №20
    [5, 25] = кошельки с №5 по №25

    ACCOUNTS_IN_STREAM      | Количество кошельков в потоке на выполнение. Если всего 100 кошельков, а указать 10,
                                то софт сделает 10 подходов по 10 кошельков
    CONTROL_TIMES_FOR_SLEEP | Количество проверок, после которого для всех аккаунтов будет включен рандомный сон в
                                моменте, когда газ опуститься до MAXIMUM_GWEI и аккаунты продолжат работать

    EXCEL_PASSWORD          | Включает запрос пароля при входе в софт. Сначала установите пароль в таблице
    EXCEL_PAGE_NAME         | Название листа в таблице. Пример: 'zkSync'
    GOOGLE_SHEET_URL        | Ссылка на вашу Google таблицу с прогрессом аккаунтов
    GOOGLE_SHEET_PAGE_NAME  | Аналогично EXCEL_PAGE_NAME
"""
GLOBAL_NETWORK = 11              # 26.12.2023 поддерживается все сети из OMNI-CHAIN CONTROL
SOFTWARE_MODE = 0                # 0 - последовательный запуск / 1 - параллельный запуск
ACCOUNTS_IN_STREAM = 1           # Только для SOFTWARE_MODE = 1 (параллельный запуск)
WALLETS_TO_WORK = 0              # 0 / 3 / 3, 20 / [3, 20]
SHUFFLE_WALLETS = False          # Перемешивает кошельки перед запуском
SHUFFLE_ROUTE = False            # Перемешивает маршрут перед запуском
BREAK_ROUTE = False              # Прекращает выполнение маршрута, если произойдет ошибка
SAVE_PROGRESS = True             # True или False | Включает сохранение прогресса аккаунта для Classic-routes
TELEGRAM_NOTIFICATIONS = False   # True или False | Включает уведомления в Telegram

'------------------------------------------------SLEEP CONTROL---------------------------------------------------------'
SLEEP_MODE = False               # True или False | Включает сон после каждого модуля и аккаунта
SLEEP_TIME = (10, 15)            # (минимум, максимум) секунд | Время сна между модулями.
SLEEP_TIME_STREAM = (10, 20)     # (минимум, максимум) секунд | Время сна между аккаунтами.

'-------------------------------------------------GAS CONTROL----------------------------------------------------------'
GAS_CONTROL = False             # True или False | Включает контроль газа
MAXIMUM_GWEI = 40               # Максимальный GWEI для работы софта, изменять во время работы софта в maximum_gwei.json
SLEEP_TIME_GAS = 100            # Время очередной проверки газа
CONTROL_TIMES_FOR_SLEEP = 5     # Количество проверок
GAS_MULTIPLIER = 1.5            # Множитель газа для транзакций

'------------------------------------------------RETRY CONTROL---------------------------------------------------------'
MAXIMUM_RETRY = 3               # Количество повторений при ошибках
SLEEP_TIME_RETRY = (5, 10)      # (минимум, максимум) секунд | Время сна после очередного повторения

'------------------------------------------------PROXY CONTROL---------------------------------------------------------'
USE_PROXY = False                # True или False | Включает использование прокси
MOBILE_PROXY = False             # True или False | Включает использование мобильных прокси. USE_PROXY должен быть True
MOBILE_PROXY_URL_CHANGER = ['',
                            '',
                            '']  # ['link1', 'link2'..] | Ссылки для смены IP

'-----------------------------------------------SLIPPAGE CONTROL-------------------------------------------------------'
SLIPPAGE = 2                    # 0.54321 = 0.54321%, 1 = 1% | Slippage, на сколько % вы готовы получить меньше
PRICE_IMPACT = 3                # 0.54321 = 0.54321%, 1 = 1% | Максимальное влияние на цену при обменах токенов

'-----------------------------------------------APPROVE CONTROL--------------------------------------------------------'
UNLIMITED_APPROVE = False       # True или False Включает безлимитный Approve для контракта

'------------------------------------------------SECURE DATA-----------------------------------------------------------'
# OKX API KEYS https://www.okx.com/ru/account/my-api
OKX_API_KEY = ""
OKX_API_SECRET = ""
OKX_API_PASSPHRAS = ""

# BINGX API KEYS https://bingx.com/ru-ru/account/api/
BINGX_API_KEY = ""
BINGX_API_SECRET = ""

# BINANCE API KEYS https://www.binance.com/ru/my/settings/api-management
BINANCE_API_KEY = ""
BINANCE_API_SECRET = ""

# EXCEL AND GOOGLE INFO
EXCEL_PASSWORD = False
EXCEL_PAGE_NAME = ""
GOOGLE_SHEET_URL = ""
GOOGLE_SHEET_PAGE_NAME = ""

# TELEGRAM DATA
TG_TOKEN = ""  # https://t.me/BotFather
TG_ID = ""  # https://t.me/getmyid_bot

# INCH API KEY https://portal.1inch.dev/dashboard
ONEINCH_API_KEY = ""

# LAYERSWAP API KEY https://www.layerswap.io/dashboard
LAYERSWAP_API_KEY = ""
