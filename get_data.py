import MetaTrader5 as mt5
import pandas as pd

from config.settings import (
    BACKTEST_START,
    BACKTEST_DATA_DIR,
    EMA_WARMUP_DIR,
    EMA_WARMUP_CANDLES,
    H1_DATA_FILE,
    H4_DATA_FILE,
    H1_WARMUP_FILE,
    H4_WARMUP_FILE,
    SYMBOL,
    EXPECTED_SERVER_TEXT,
)



def download_candles(timeframe, timeframe_name, price_digits):
    """ Download historical candles adn split them into warm-up and backtest data."""

    # Request sufficient history before the backtest start.
    # One extra year provides a generous buffer for collecting warm-up candles.

    backtest_start = pd.Timestamp(BACKTEST_START)

    request_start = (
        backtest_start - pd.Timedelta(days=365)
    ).to_pydatetime()

    # Use current UTC time as the request endpoint.
    request_end = pd.Timestamp.now(tz="UTC").to_pydatetime()

    rates = mt5.copy_rates_range(
        SYMBOL,
        timeframe,
        request_start,
        request_end,
    )
    if rates is None or len(rates) == 0:
        raise RuntimeError(
            f"No {timeframe_name} candles received for {SYMBOL}. "
            f"MT5 error: {mt5.last_error()}"
        )

    df = pd.DataFrame(rates)

    # Convert Unix timestamps to UTC-aware pandas timestamps.
    df["time"] = pd.to_datetime(
        df["time"],
        unit="s",
        utc=True,
    )

    # Sort oldest to newest and remove duplicate timestamps.
    # Duplicates are unexpected, so fail rather than silently remove them.
    df = df.sort_values("time").reset_index(drop=True)

    if df["time"].duplicated().any():
        raise ValueError(
            f"Duplicate timestamps found in downloaded {timeframe_name} data."
        )
    # Exclude any candle that has not fully closed.
    # MT5 timestamps identify the candle's opening time.
    candle_duration = {
        mt5.TIMEFRAME_H1: pd.Timedelta(hours=1),
        mt5.TIMEFRAME_H4: pd.Timedelta(hours=4),
    }[timeframe]

    now_utc = pd.Timestamp.now(tz="UTC")

    df = df[
        df["time"] + candle_duration <= now_utc
    ].copy()

    df = df.reset_index(drop=True)

    if df.empty:
        raise RuntimeError(
            f"No completed {timeframe_name} candles are available."
        )

    # Split at the exact backtest start timestamp.
    warmup_data = df[df["time"] < backtest_start].tail(
        EMA_WARMUP_CANDLES
    ).copy()

    backtest_data = df[df["time"] >= backtest_start].copy()

    # Do not continue if there is insufficient warm-up history.
    if len(warmup_data) < EMA_WARMUP_CANDLES:
        raise RuntimeError(
            f"Insufficient {timeframe_name} warm-up data. "
            f"Required: {EMA_WARMUP_CANDLES}; "
            f"received: {len(warmup_data)}. "
            "Check MT5 history availability."
        )

    if backtest_data.empty:
        raise RuntimeError(
            f"No {timeframe_name} candles found on or after "
            f"{backtest_start}."
        )

    # Round prices to the symbol's reported decimal precision.
    price_columns = ["open", "high", "low", "close"]

    for data in (warmup_data, backtest_data):
        data.loc[:, price_columns] = data[price_columns].round(
            price_digits
        )

    # Save to the paths defined in config/settings.py.
    warmup_path, backtest_path = {
        mt5.TIMEFRAME_H1: (H1_WARMUP_FILE, H1_DATA_FILE),
        mt5.TIMEFRAME_H4: (H4_WARMUP_FILE, H4_DATA_FILE),
    }[timeframe]

    warmup_path.parent.mkdir(parents=True, exist_ok=True)
    backtest_path.parent.mkdir(parents=True, exist_ok=True)

    warmup_data.to_csv(warmup_path, index=False)
    backtest_data.to_csv(backtest_path, index=False)

    print(f"\n{'=' * 55}")
    print(f"{timeframe_name} DATA DOWNLOAD")
    print(f"{'=' * 55}")

    print(f"Warm-up file: {warmup_path}")
    print(f"Warm-up candles: {len(warmup_data)}")
    print(f"Warm-up first candle: {warmup_data['time'].iloc[0]}")
    print(f"Warm-up last candle:  {warmup_data['time'].iloc[-1]}")

    print(f"\nBacktest file: {backtest_path}")
    print(f"Backtest candles: {len(backtest_data)}")
    print(f"Backtest first candle: {backtest_data['time'].iloc[0]}")
    print(f"Backtest last candle:  {backtest_data['time'].iloc[-1]}")

    print("\nLatest 5 backtest candles:")
    print(
        backtest_data[
            ["time", "open", "high", "low", "close"]
        ].tail().to_string(index=False)
    )

    return warmup_data, backtest_data



def main():
    """Connect to MT5 and download H1/H4 historical datasets."""

    BACKTEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
    EMA_WARMUP_DIR.mkdir(parents=True, exist_ok=True)

    if not mt5.initialize():
        raise RuntimeError(
            f"MT5 initialization failed: {mt5.last_error()}"
        )

    try:
        # Verify the connected account and broker server.
        account = mt5.account_info()

        if account is None:
            raise RuntimeError(
                "No account is connected to the MT5 terminal."
            )

        print("Connected account:", account.login)
        print("Connected server:", account.server)
        print("Company:", account.company)

        if (
            not account.server
            or EXPECTED_SERVER_TEXT.lower() not in account.server.lower()
        ):
            raise RuntimeError(
                f"Safety check failed. Expected a server containing "
                f"'{EXPECTED_SERVER_TEXT}', but connected to "
                f"'{account.server}'. No download performed."
            )

        # Verify and select the exact broker symbol.
        symbol_info = mt5.symbol_info(SYMBOL)

        if symbol_info is None:
            raise RuntimeError(
                f"Symbol '{SYMBOL}' was not found in MT5. "
                "Check its exact name in Market Watch."
            )

        if not mt5.symbol_select(SYMBOL, True):
            raise RuntimeError(
                f"Could not select {SYMBOL}: {mt5.last_error()}"
            )

        price_digits = symbol_info.digits

        print("Selected symbol:", SYMBOL)
        print("Price digits:", price_digits)
        print("Backtest starts at:", BACKTEST_START)
        print("Warm-up candles per timeframe:", EMA_WARMUP_CANDLES)

        # Download and split each timeframe independently.
        download_candles(
            mt5.TIMEFRAME_H1,
            "H1",
            price_digits,
        )

        download_candles(
            mt5.TIMEFRAME_H4,
            "H4",
            price_digits,
        )

        print("\nHistorical data download completed successfully.")

    finally:
        mt5.shutdown()


if __name__ == "__main__":
    main()
