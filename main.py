import MetaTrader5 as mt5

if not mt5.initialize():
    print("Initialization failed:", mt5.last_error())
    raise SystemExit

try:
    terminal = mt5.terminal_info()
    account = mt5.account_info()

    print("Terminal:", terminal)

    if account is None:
        print("No account information available:", mt5.last_error())
    else:
        print("Account login:", account.login)
        print("Broker server:", account.server)
        print("Company:", account.company)
        print("Trade allowed:", account.trade_allowed)

finally:
    mt5.shutdown()


    