import json
import time 
import pandas as pd
import sys

import asyncio 
import numpy as np
#import asnycio 
from bitshares import BitShares
from bitshares.account import Account
from bitshares.market import Market

from utils import *
from tinydb import Query, TinyDB
from async_Manager import Manager
    
class Worker(Manager):
    def __init__(self, **kwargs):
        data = {
            'tradingside' : 
            'market_key' : 
            'instance' : 
            'base' : 
            'quote'
            '2Quote' : 
            'tsize' : 
            'loop' : 
            'queue' : 
        }
        #quote, base, account, strategy, toQuote, queue, 
        kwargs['queue'] = Queue(loop=kwargs['loop'])
        
        for key, arg in kwargs.items():
            setattr(self, key, arg)
        self.market = Market(self.market_key, block_instance = instance)
        kwargs.update({'market' :self.market})
        self.strategy = CheckSpread(**kwargs)
        super().__init__(**kwargs)

    async def run(self, **kwargs):
        i = 0
        print("Starting to run on {}".format(self.market_key))
        while True:
            await asyncio.sleep(np.random.randint(10)) 
            i += 1
            if not i%5:
                print("{} after {} iterations".format(self.market_key, i)) 
            asks, bids = self.orderbook
            event = self.strategy.apply(asks, bids)
            if event:
                queue.put_nowait(event)
            await asyncio.sleep(5)
