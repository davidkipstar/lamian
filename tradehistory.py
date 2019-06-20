from bitshares.market import Market

m = Market('BRIDGE.SINS:BRIDGE.BTC')
tradehistory = m.trades()
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


print(trade_l)
print(own_buys)
print(own_sells)