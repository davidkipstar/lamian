# download binance orderbooks and trades for new price calculation, where
# volume ~ liquidity
import keyring
from binance.client import Client

# keyring.set_password("system", "username", "password")
# keyring.get_password("system", "username")

api_key = keyring.get_password('')
api_secret = keyring.get_password('')

client = Client(api_key, api_secret)

# get all symbol prices
tickers = client.get_all_tickers()

for sym in tickers:
    symdepth = client.get_order_book(symbol = sym)
    

#list(map(client.get_order_book, mylist))

# get market depth
#depth = client.get_order_book(symbol='BNBBTC')

