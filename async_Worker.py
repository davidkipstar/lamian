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

    
class Worker:
    worker_counter = 0 

    def __init__(self, quote, base, account, instance, **kwargs): 
        #
        self.instance = instance
        self.orderbooklimit = 25
        self.history = []
        self.pw = "5KgkgfK4suQqLJY1Uv8mY4tPx4e8V8a2q2SX8xbS5o8UN9rxBJJ"
        self.acc = "kipstar1337"
        for key, arg in kwargs.items():
            setattr(self, key, arg)
        
        #
        self.db = TinyDB('2DAY.json')
        self.db_template = {'market': self.market_key, 
                            'timestamp' : time.time() ,
                            'asks' : None, 
                            'bids' : None }

        self.id = Worker.worker_counter
        Worker.worker_counter += 1
        #
        print("Market_key: {}".format(self.market_key))
        self.market = Market(self.market_key, block_instance = self.instance)
        #This should always be the same thus BTC:GIN and GIN:BTC both yield BTC:GIN
        #self.market_key = self.market.get_string
        self.cur = quote        
        self.market.bitshares.wallet.unlock(self.pw)
        
    @classmethod
    def from_manager(cls, manager, instance,**kwargs):
        return cls(manager.buy, manager.sell, manager.account, instance, **kwargs) 


    async def run(self, tradingside = 'buy'):
        i = 0
        assert(self.queues)
        print("Starting to run on {}".format(self.market_key))
        while True:
            await asyncio.sleep(np.random.randint(10)) 
            i += 1
            if not i%5:
                print("{} after {} iterations".format(self.market_key, i)) 
            orderbook = self.market.orderbook(self.orderbooklimit)
            new_entry = self.db_template.copy()
            new_entry['bids'] = orderbook['bids']
            new_entry['asks'] = orderbook['asks']
            self.db.insert(new_entry)
            for queue in self.queues:
                queue.put_nowait(new_entry)
            await asyncio.sleep(5)
