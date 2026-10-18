
import pandas as pd

from config.settings import (
    H1_DATA_FILE,
    H4_DATA_FILE,
    H1_WARMUP_FILE,
    H4_WARMUP_FILE,
    BACKTEST_START,
    EMA_WARMUP_CANDLES,
)

# Columns expected in our MT5 historical candle files
REQUIRED_COLUMNS = [
    "time",
    "open",
    "high",
    "low",
    "close",
    "tick_volume",
    "spread",
    "real_volume",
]

PRICE_COLUMNS = ["open", "high", "low", "close"]


def load_candles(file_path):
    """
    Load and validate historical candle data from a CSV file.

    Returns:
        pandas.DataFrame: Validated, chronologically sorted candles.
    """

    # 1. Check that the file exists and contains readable CSV data.
    try:
        df = pd.read_csv(file_path)

    except FileNotFoundError as exc:
        raise RuntimeError(
            f"File not found: {file_path}. "
            "Please download the historical data first."
        ) from exc

    except pd.errors.EmptyDataError as exc:
        raise ValueError(
            f"File is empty: {file_path}"
        ) from exc

    if df.empty:
        raise ValueError(
            f"File is empty: {file_path}. "
            "Please download the historical data first."
        )

    # 2. Verify that all required columns are present.
    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns in {file_path}: "
            f"{missing_columns}"
        )

    # 3. Parse timestamps as UTC-aware datetimes.
    df["time"] = pd.to_datetime(
        df["time"],
        utc=True,
        errors="coerce",
    )

    if df["time"].isna().any():
        raise ValueError(
            f"Invalid timestamps found in: {file_path}"
        )

    # 4. Convert market data columns to numeric values.
    numeric_columns = [
        "open",
        "high",
        "low",
        "close",
        "tick_volume",
        "spread",
        "real_volume",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

        if df[column].isna().any():
            raise ValueError(
                f"Invalid numeric values in column "
                f"'{column}' of {file_path}"
            )

    # 5. Reject duplicate candle timestamps.
    if df["time"].duplicated().any():
        raise ValueError(
            f"Duplicate candle timestamps found in: {file_path}"
        )

    # 6. Reject invalid prices, volumes, and spreads.
    if (df[PRICE_COLUMNS] <= 0).any().any():
        raise ValueError(
            f"Non-positive OHLC prices found in: {file_path}"
        )

    if (
        df[["tick_volume", "spread", "real_volume"]] < 0
    ).any().any():
        raise ValueError(
            f"Negative volume or spread values found in: {file_path}"
        )

    # The high must be at least as high as every OHLC price.
    if (
        df["high"]
        < df[["open", "low", "close"]].max(axis=1)
    ).any():
        raise ValueError(
            f"Invalid candle high values found in: {file_path}"
        )

    # The low must be at most as low as every OHLC price.
    if (
        df["low"]
        > df[["open", "high", "close"]].min(axis=1)
    ).any():
        raise ValueError(
            f"Invalid candle low values found in: {file_path}"
        )

    # 7. Sort candles from oldest to newest.
    df = df.sort_values("time").reset_index(drop=True)

    return df


def validate_data_period(
    warmup_data,
    backtest_data,
    timeframe_name,
):
    """
    Ensure warm-up data precedes the backtest period.
    """

    backtest_start = pd.Timestamp(BACKTEST_START)

    if len(warmup_data) != EMA_WARMUP_CANDLES:
        raise ValueError(
            f"{timeframe_name} warm-up data must contain "
            f"{EMA_WARMUP_CANDLES} candles; "
            f"found {len(warmup_data)}."
        )

    if warmup_data["time"].max() >= backtest_start:
        raise ValueError(
            f"{timeframe_name} warm-up data contains "
            "candles at or after the backtest start."
        )

    if backtest_data["time"].min() < backtest_start:
        raise ValueError(
            f"{timeframe_name} backtest data contains "
            "candles before the backtest start."
        )

    if warmup_data["time"].max() >= backtest_data["time"].min():
        raise ValueError(
            f"{timeframe_name} warm-up and backtest periods "
            "overlap or are out of order."
        )


def print_data_summary(name, df):
    """Print a short summary of a dataset."""

    print(f"\n{name}:")
    print(f"Number of candles: {len(df)}")
    print(f"First candle: {df['time'].iloc[0]}")
    print(f"Last candle:  {df['time'].iloc[-1]}")


def load_market_data():
    """
    Load warm-up and backtest data for both H1 and H4.

    Returns:
        tuple: (h1_warmup, h1_backtest, h4_warmup, h4_backtest)
    """

    # Load and validate all four CSV files.
    h1_warmup = load_candles(H1_WARMUP_FILE)
    h4_warmup = load_candles(H4_WARMUP_FILE)

    h1_backtest = load_candles(H1_DATA_FILE)
    h4_backtest = load_candles(H4_DATA_FILE)

    # Check that the warm-up and backtest periods are separated.
    validate_data_period(
        h1_warmup, h1_backtest, "H1"
    )

    validate_data_period(
        h4_warmup, h4_backtest, "H4"
    )

    print("\nHistorical data loaded and validated successfully.")

    print_data_summary("H1 warm-up data", h1_warmup)
    print_data_summary("H1 backtest data", h1_backtest)

    print_data_summary("H4 warm-up data", h4_warmup)
    print_data_summary("H4 backtest data", h4_backtest)

    return (
        h1_warmup,
        h1_backtest,
        h4_warmup,
        h4_backtest,
    )
