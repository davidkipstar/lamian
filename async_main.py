import os 
import time 
import asyncio

from async_Manager import Manager
from async_Worker import Worker

#setup 
m = Manager()
"""
sellcoins = m.pick_sellcoins()
print(sellcoins)

for coin in sellcoins.values():
    market = 'BRIDGE.BTC:'+ getattr(coin,'symbol')
    Worker(market, sellcoins[coin.symbol].amount - 0.00001, btc=False)
    time.sleep(1)


btcbalance = m.balances['BRIDGE.BTC']
buycoins = ['LCC', 'LPC']

for coin in buycoins:
    #tually have this coin
    market = 'BRIDGE.{}:BRIDGE.BTC'.format(coin)
    tsize = 0.001
    Worker(market, tsize)
    #check if true
    btcbalance = btcbalance - tsize
    time.sleep(1)
"""
coin= 'GIN'
market = 'BRIDGE.BTC:BRIDGE.{}'.format(coin)
tsize = 0.0001
w = Worker(market, tsize,th = 0.002)
w.run()