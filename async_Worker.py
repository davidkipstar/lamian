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
                print('Event:', x)
                self.logger.info("Event created")
                self.queue.put_nowait(x)
            await asyncio.sleep(5)
