
from pathlib import Path

# ==================================================
# PROJECT PATHS
# ==================================================

PROJECT_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_DIR / "data"

# Historical candles used only to initialize indicators
EMA_WARMUP_DIR = DATA_DIR / "ema_warmup"

# Historical candles used for backtesting
BACKTEST_DATA_DIR = DATA_DIR / "backtest_data"


# ==================================================
# HISTORICAL DATA FILES
# ==================================================

H1_WARMUP_FILE = EMA_WARMUP_DIR / "eurusd_h1.csv"
H4_WARMUP_FILE = EMA_WARMUP_DIR / "eurusd_h4.csv"

H1_DATA_FILE = BACKTEST_DATA_DIR / "eurusd_h1.csv"
H4_DATA_FILE = BACKTEST_DATA_DIR / "eurusd_h4.csv"


# ==================================================
# BACKTEST PERIOD
# ==================================================

BACKTEST_START = "2023-01-01 00:00:00+00:00"


# ==================================================
# MARKET SETTINGS
# ==================================================

SYMBOL = "EURUSDm"



# Number of closed candles before the backtest start
# used for EMA warm-up.
EMA_WARMUP_CANDLES = 500

# EURUSD standard pip size
PIP_SIZE = 0.0001


# ==================================================
# INDICATOR SETTINGS
# ==================================================

FAST_EMA_PERIOD = 20
SLOW_EMA_PERIOD = 50


# ==================================================
# RISK MANAGEMENT
# ==================================================

RISK_PER_TRADE = 0.005  # 0.5% planned account risk per trade
MAX_OPEN_POSITIONS = 6
REWARD_RISK_RATIO = 2.0


# ==================================================
# BACKTESTING
# ==================================================

INITIAL_BALANCE = 100000.0


# ==================================================
# EXECUTION SAFETY
# ==================================================

EXPECTED_SERVER_TEXT = "Exness"

# Keep real trading disabled during development and backtesting.
LIVE_TRADING_ENABLED = False
