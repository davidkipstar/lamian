import os 
import time 
import asyncio

from async_Manager import Manager
from async_Worker import Worker


if __name__ == '__main__':
    #setup 
    #BUY
    coin= 'LGS'
    market = 'BRIDGE.{}:BRIDGE.BTC'.format(coin)

    tsize = 0.0000001
    w = Worker(market, tsize,th = 0.0138)
    w.run()
