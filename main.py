import os 
import time 

from utils import *

from manager import Worker
from manager import Manager

if __name__ == '__main__':

    #setup 
    m = Manager('credentials.json')
    m.signup()
    m.initial_balance()

    sellcoins = m.pick_sellcoins()
    print(sellcoins)
    #sell_markets = [
    
    # 
    #for coin in sellcoins.values():
    #    market = 'BRIDGE.BTC:BRIDGE.'+ getattr(coin,'symbol')
    #    m.add_worker(market, sellcoins[coin.symbol].amount - 0.00001, btc=False)

    btcbalance = m.balances['BRIDGE.BTC']
    buycoins = ['LRM', 'LPC']
    for coin in buycoins:
        market = 'BRIDGE.{}:BRIDGE.BTC'.format(coin)
        tsize = 0.001
        m.add_worker(market, tsize)
        #check if true
        btcbalance = btcbalance - tsize

    m.start()

    while m.listen():
        #
        x = m.q.get()
        print(x)

    
