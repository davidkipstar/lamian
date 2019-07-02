from bitshares.account import Account
import time

account = Account("sxmoli9")

other_balance = []
iteration = 0

while len(other_balance) != 1:

    # Query at the same time...
    current_orders = account.openorders
    current_balances = account.balances

    # Balance in orders

    buy_orders = list(filter(lambda x: x['quote']['symbol'] == 'BRIDGE.BTC', current_orders))
    quote_inventory_in_buys = sum(list(map(lambda x: x['quote']['amount'], buy_orders)))

    sell_orders = list(filter(lambda x: x['quote']['symbol'] != 'BRIDGE.BTC' and x['quote']['symbol'] != 'OPEN.BTC', current_orders))
    quote_inventory_in_sells = sum(list(map(lambda x: x['base']['amount'], sell_orders)))

    open_btc_orders = list(filter(lambda x: x['quote']['symbol'] == 'OPEN.BTC', current_orders))

    # BTC balance
    btc_balance = list(filter(lambda x: x['symbol'] == 'BRIDGE.BTC', current_balances))
    btc_amount = btc_balance[0]['amount'] + open_btc_orders[0]['quote']['amount']

    # Remaining Balances
    other_balance = list(filter(lambda x: x['symbol'] != 'BRIDGE.BTC' and x['amount'] > 0.021, current_balances))

    print(other_balance)
    print('trying to catch a clean balance...')
    iteration += 1
    time.sleep(2)

pf_market_value = quote_inventory_in_buys + quote_inventory_in_sells + btc_amount
print('pf market value: ', pf_market_value)
print('further balances: ', other_balance) # todo: give weight using market value!

print('current_orders: ', current_orders)
print('current_balances: ', current_balances)

