import os 
import time 
import asyncio

from async_Manager import Manager
from async_Worker import Worker

from Strategy import CheckSpread

if __name__ == '__main__':
    
    coin= 'LGS'
    market = 'BRIDGE.{}:BRIDGE.BTC'.format(coin)
    #
    tsize = 0.0000001
    side = 'sell'
    s = CheckSpread(tradingside = side)
    m = Manager(['BTC','LGS','LCC'])
    #
    w = Worker(quote = 'LCC', base = 'BTC', th = 0.0138, tradingside = side, tsize = 0.00000001)
    #
    w.run()
