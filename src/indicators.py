
import pandas as pd

from config.settings import PIP_SIZE, FAST_EMA_PERIOD, SLOW_EMA_PERIOD


def add_indicators(df):
    """
    Calculate EMA 20, EMA 50, and the gap between them.
    """

    df = df.copy()

    df["ema20"] = df["close"].ewm(
        span=FAST_EMA_PERIOD,
        adjust=False,
    ).mean()

    df["ema50"] = df["close"].ewm(
        span=SLOW_EMA_PERIOD,
        adjust=False,
    ).mean()

    df["ema_gap_pips"] = (
        (df["ema20"] - df["ema50"]).abs() / PIP_SIZE
    )

    return df


def add_backtest_indicators(warmup_data, backtest_data):
    """
    Use warm-up candles to initialize indicators,
    then return the backtest candles with indicators.
    """

    combined_data = pd.concat(
        [warmup_data, backtest_data],
        ignore_index=True,
    )

    combined_data = combined_data.sort_values(
        "time"
    ).reset_index(drop=True)

    combined_data = add_indicators(combined_data)

    backtest_start = backtest_data["time"].min()

    backtest_with_indicators = combined_data[
        combined_data["time"] >= backtest_start
    ].copy()

    return backtest_with_indicators.reset_index(drop=True)
