import pandas as pd

# Pattern thresholds

STRONG_BODY_RATIO = 0.65
SMALL_BODY_RATIO = 0.25

VOLUME_LOOKBACK = 20
ATR_PERIOD = 20
EXTREME_CANDLE_ATR_MULTIPLE = 3.0

def add_candlestick_patterns(df):
    """
    Detect unified bullish and bearish engulfing signals.

    A signal can form through:
    1. Classic real-body engulfment.
    2. A small-bodied candle followed by a strong
       directional candle.

    Both setups require volume confirmation.
    Extreme candles are flagged, not automatically rejected.
    """

    df = df.copy()

    #1 Calculate the candle body full range

    df["candle_body"] = (df["close"] - df["open"]).abs()
    df["candle_range"] = (df["high"] - df["low"])

    # Avoid division by zero for candles with no range.
    df["body_ratio"] = (
        df["candle_body"]
        / df["candle_range"].replace(0, float("nan"))
    )

    # 2. Identify bullish and bearish candles.
    bullish = df["close"] > df["open"]
    bearish = df["close"] < df["open"]
    previous_bullish = bullish.shift(1, fill_value=False)
    previous_bearish = bearish.shift(1, fill_value=False)


    # 3. Identify small-bodied and strong candles.
    small_previous_body = (
        df["body_ratio"].shift(1) <= SMALL_BODY_RATIO
    )

    strong_current_body = (
        df["body_ratio"] >= STRONG_BODY_RATIO
    )

    # 4. Classic bullish engulfing.
    classic_bullish = (
        previous_bearish
        & bullish
        & (df["open"] <= df["close"].shift(1))
        & (df["close"] >= df["open"].shift(1))
    )


    # 5. Classic bearish engulfing.
    classic_bearish = (
        previous_bullish
        & bearish
        & (df["open"] >= df["close"].shift(1))
        & (df["close"] <= df["open"].shift(1))
    )


    # 6. Strong candle following a small-bodied candle.
    indecision_bullish = (
        small_previous_body
        & bullish
        & strong_current_body
    )

    indecision_bearish = (
        small_previous_body
        & bearish
        & strong_current_body
    )

    # 7. Compare current tick volume with the previous
    # 20 candles only (excluding the current candle).
    df["average_tick_volume_20"] = (
        df["tick_volume"]
        .shift(1)
        .rolling(window=VOLUME_LOOKBACK, min_periods=VOLUME_LOOKBACK)
        .mean()
    )

    df["volume_confirmed"] = (
        df["tick_volume"] > df["average_tick_volume_20"]
    )

    # 8. Combine both pattern types into unified signals.
    df["bullish_engulfing"] = (
        (classic_bullish | indecision_bullish)
        & df["volume_confirmed"]
    )

    df["bearish_engulfing"] = (
        (classic_bearish | indecision_bearish)
        & df["volume_confirmed"]
    )

    # 9. Calculate ATR(20) to identify unusually large candles.
    previous_close = df["close"].shift(1)

    true_range = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - previous_close).abs(),
            (df["low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    df["atr_20"] = true_range.rolling(
        window=ATR_PERIOD,
        min_periods=ATR_PERIOD,
    ).mean()

    df["extreme_candle"] = (
        df["candle_range"]
        > EXTREME_CANDLE_ATR_MULTIPLE * df["atr_20"]
    )

    return df
