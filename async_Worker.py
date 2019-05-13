import json
import time 
import sys
import logging
import asyncio 
import pandas as pd
import numpy as np
import sys 
import re 

from async_Manager import Manager
from Strategy import CheckSpread

from utils import *
from tinydb import Query, TinyDB
from asyncio import Queue

from bitshares import BitShares
from bitshares.account import Account
from bitshares.market import Market

    
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
    def __init__(self, loop, logger ,**kwargs):

        for key, arg in kwargs.items():
            setattr(self, key, arg)
        #setup logger
        self.logger = logging.getLogger("{}_{}".format(__name__, re.sub('BRIDGE.','',self.market_key)))
        # wenn tsize = 0 und tradignside == 'sell' in kwargs dann erstmal sleep und anschliessend immer balance testen. wenn > 0.01 dann verkaufen
        while self.tsize == 0:
            # These are actually functions from the Analyst, how do I call them in here without redefinition?
            print('zzzzzzzzzz... sleeping because no balance ', self.tradingside)
            time.sleep(10)
            # Check if balance changed, and if true, start trading
            self.account = Account(self.acc)
            self.account.refresh()
            my_coins = self.account.balances
            self.balance = dict(zip(map(lambda x: getattr(x,'symbol'),my_coins),my_coins))
            try:
                self.major_balance = self.balance['BRIDGE.GIN']
            except:
                self.major_balance = 0
            if self.major_balance > 0.01:
                tsize = self.major_balance
            else:
                tsize = 0
        
        self.market = Market(self.market_key, block_instance = self.instance)
        kwargs['market'] = self.market
        self.queue = Queue(loop = loop)
        self.strategy = CheckSpread.from_kwargs(logger, **kwargs)

    async def run(self, **kwargs):
        i = 0
        self.logger.info("Worker starts on {}".format(re.sub('BRIDGE.','',self.market_key)))
        while True:
            await asyncio.sleep(np.random.randint(10)) 
            i += 1
            if not i%5:
                self.logger.info("{} iterations".format(i)) 
            event = self.strategy.apply()#asks, bids)
            
            if event:
                x = await event
                #print('Event:', x)
                self.logger.info("Event created {}".format(x))
                if x:
                    self.queue.put_nowait(x)
            await asyncio.sleep(5)
