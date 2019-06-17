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
    """
    def __init__(self, loop, logger ,**kwargs):

        for key, arg in kwargs.items():
            setattr(self, key, arg)
        if self.tradingside == 'sell': 
            self.market_key = "{}:{}".format(self.sell, self.major_coin)
        else:
            self.market_key = "{}:{}".format(self.buy, self.major_coin)
        #if self.tradingside == 'buy': self.market_key = "{}:{}".format(self.major_coin, self.buy)
        self.logger = logging.getLogger("{}_{}".format(__name__, re.sub('BRIDGE.','',self.market_key)))
        self.market = Market(self.market_key, block_instance = self.instance)
        kwargs['market'] = self.market
        self.queue = Queue(loop = loop)
        kwargs.update({'market_key' : self.market_key})
        self.logger.info("Created worker {} on {}".format(self.tradingside, self.market_key))
        self.strategy = CheckSpread.from_kwargs(logger, **kwargs)

    @classmethod
    def from_kwargs(cls, *args, **kwargs):

        return cls(*args, **kwargs)
    async def run(self, **kwargs):
        i = 0
        self.logger.info("Worker starts on {}".format(re.sub('BRIDGE.','',self.market_key)))
        while True:
            await asyncio.sleep(0.000000001)
            i += 1
            event = self.strategy.apply()
            
            if event:
                x = await event
                self.logger.info("Event created {}".format(x))
                if x:
                    self.queue.put_nowait(x)
            
            await asyncio.sleep(0.000000001)
