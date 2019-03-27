import os 
import time 
import asyncio

from async_Manager import Manager
from async_Worker import Worker
"""
from Strategy import CheckSpread
class Worker:
    def __init__(self, q , r, s , **kwargs):
        self.q = q
    
    async def run(self):

        while True:
            print(self.q)
            await asyncio.sleep(3)
"""

async def main(workers):
    res = await asyncio.gather(*(w.run() for w in workers))#
    return res 

if __name__ == '__main__':
    
    coin= 'LGS'
    market = 'BRIDGE.{}:BRIDGE.BTC'.format(coin)
    #
    tsize1 = 0.0000001
    tsize2 = 0.0000001
    w1 = Worker('LGS', 'BTC', tsize1, th = 0.0138, tradingside = 'buy')
    w2 = Worker('BTC', 'LGS', tsize2, th = 0.0138, tradingside = 'buy' )
    #ManagerStrategy
    m = Manager()
    m.workers = w1
    m.workers = w2

    while True:
        res = asyncio.run(m.run())
