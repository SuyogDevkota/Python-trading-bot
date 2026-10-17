from pathlib import Path
import pandas as pd
import MetaTrader5 as mt5


# ----------------------------
# SETTINGS
# ----------------------------

SYMBOL = "EURUSDm"  # Symbol to download candles for.1
# Number of completed candles to download for each timeframe.
H1_CANDLE_COUNT = 5000
H4_CANDLE_COUNT = 2000

# Safety check: only download while connected to an Exness account.
EXPECTED_SERVER_TEXT = "Exness"

# Always save files inside this project's data folder,
# regardless of which directory the terminal starts in.
PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"

DATA_DIR.mkdir(parents=True, exist_ok=True)


def download_candles(timeframe, count, filename):
    """
    Download candles from MetaTrader 5 and save them to a CSV file
    """
    rates = mt5.copy_rates_from_pos(SYMBOL, timeframe, 1, count)

    """
    Rates is returned by mt5 terminal as a numpy array of tuples. Each tuple contains the following fields:
    (time, open, high, low, close, tick_volume, spread, real_volume)

    it takes the parameters:
    - symbol: the symbol to download candles for (e.g., "EURUSD")
    - timeframe: the timeframe to download candles for (e.g., mt5.TIMEFRAME_H1 for 1-hour candles)
    - start_pos: the starting position to download candles from (1 means the most recent candle


    example:
        (1792101600, 1.16500, 1.16800, 1.16400, 1.16700, 850, 12, 0)
        (time, open, high, low, close, tick_volume, spread, real_volume)
        multiple tuples are returned in a numpy array, one for each candle.
    """

    if rates is None or len(rates) == 0:
        raise RuntimeError(
            f"No candles received for {SYMBOL}. "
            f"MT5 error: {mt5.last_error()}"
        )


    df = pd.DataFrame(rates)

    df["time"] = pd.to_datetime(df["time"], unit="s" , utc=True)


    df = df.sort_values("time").reset_index(drop=True)
    output_path = DATA_DIR / filename
    price_columns = ["open", "high", "low", "close"]
    df[price_columns] = df[price_columns].round(5)
    df.to_csv(output_path, index=False)

    print(f"\nSaved file: {output_path}")
    print(f"Candles downloaded: {len(df)}")
    print(f"First candle: {df['time'].iloc[0]}")
    print(f"Last candle:  {df['time'].iloc[-1]}")
    print("\nLatest 5 candles:")
    print(df[["time", "open", "high", "low", "close"]].tail())



def main():
    # Connect to the MT5 terminal currently running on this computer.
    if not mt5.initialize():
        raise RuntimeError(
            f"MT5 initialization failed: {mt5.last_error()}"
        )

    try:
        account = mt5.account_info()

        if account is None:
            raise RuntimeError(
                "No account is connected to the MT5 terminal."
            )

        print("Connected account:", account.login)
        print("Connected server:", account.server)
        print("Company:", account.company)
        symbols = mt5.symbols_get()
        print("Available symbols:", [symbol.name for symbol in symbols])

        # Stop rather than download from an unexpected account.
        if EXPECTED_SERVER_TEXT.lower() not in account.server.lower():
            raise RuntimeError(
                "Safety check failed: the connected server does not "
                "contain 'Exness'. Check the MT5 account before retrying."
            )

        if not mt5.symbol_select(SYMBOL, True):
            raise RuntimeError(
                f"Could not select {SYMBOL}. "
                "Check the exact symbol name in MT5."
            )

        # Download the two timeframes separately.
        download_candles(
            mt5.TIMEFRAME_H1,
            H1_CANDLE_COUNT,
            "eurusd_h1.csv"
        )

        download_candles(
            mt5.TIMEFRAME_H4,
            H4_CANDLE_COUNT,
            "eurusd_h4.csv"
        )

        print("\nDownload completed successfully.")

    finally:
        # Close the Python connection. This does not close MT5 itself.
        mt5.shutdown()


if __name__ == "__main__":
    main()