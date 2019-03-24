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
    side = 'buy'
    #s = CheckSpread(tradingside = side)
    #m = Manager(['BTC','LGS','LCC'])
    #
    w = Worker('LGS', 'BTC', tsize, th = 0.0138, tradingside = side)
    #
    w.run()
