from bitshares.market import Market

m = Market('BRIDGE.SINS:BRIDGE.BTC')
tradehistory = m.trades(limit = 100)
trade_l = []
for t in tradehistory:
    trade_l.append(t)

# trade_l is list with the recent trade history of a market
# trade_l[0]['side1_account_id'] and trade_l[0]['side2_account_id'] identifies buyer and seller
# we are '1.2.1620664'
# so just find our trades

own_id = '1.2.1620664'
own_buys = []
own_sells = []
for t in tradehistory:
    if t['side1_account_id'] == own_id:
        own_buys.append(t)
    if t['side2_account_id'] == own_id:
        own_sells.append(t)

#filtered_trades = list(filter(lambda x: x['price'] > 1, own_buys))
recent_amount_ele = list(map(lambda x: x['quote'].amount, own_buys))
recent_rate_ele = list(map(lambda x: x['price'], own_buys)) #m('price',recent_trades)


print(trade_l)
print(own_buys)
print(own_sells)