import json
import time 
import sys

import asyncio 
import pandas as pd
import numpy as np
from asyncio import Queue
#import asnycio 
from bitshares import BitShares
from bitshares.account import Account
from bitshares.market import Market

from Strategy import CheckSpread
from utils import *
from tinydb import Query, TinyDB
from async_Manager import Manager
    
class Worker:
    """
        'tradingside' : 
        'market_key' : 
        'instance' : 
        'base' : 
        'quote'
        '2Quote' : 
        'tsize' : 
        'loop' : 
        'queue' : 
    """
    def __init__(self, loop, **kwargs):

        print(kwargs)
        for key, arg in kwargs.items():

            setattr(self, key, arg)
        self.market = Market(self.market_key, block_instance = self.instance)
        kwargs['market'] = self.market
        self.queue = Queue(loop = loop)
        self.strategy = CheckSpread.from_kwargs(**kwargs)
        
    @classmethod 
    def from_kwargs(cls, loop, **kwargs):
        if kwargs['open_order']:
            print("Starting with open order")
        else:
            kwargs['state'] = 0 
        return cls(loop,**kwargs)


    @property 
    def orderbook(self):
        ob = self.market.orderbook(self.orderbooklimit)
        if len(ob['asks']) >= self.orderbooklimit and len(ob['asks']) >= self.orderbooklimit:
            asks, bids = pd.DataFrame(ob['asks']), pd.DataFrame(ob['bids'])
            return asks, bids 
        else:
            print("not liquid")
            return None, None

    async def run(self, **kwargs):
        i = 0
        print("Starting to run on {}".format(self.market_key))
        while True:
            await asyncio.sleep(np.random.randint(10)) 
            i += 1
            if not i%5:
                print("{} after {} iterations".format(self.market_key, i)) 
            #asks, bids = self.orderbook
            #print("Asks", asks)
            #print("Bids" , bids)
            event = self.strategy.apply()#asks, bids)
            if event:
                print("event")
                self.queue.put_nowait(event)
            await asyncio.sleep(5)
