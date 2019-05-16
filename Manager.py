import json
import time 
import pandas as pd
import numpy as np
import sys
import logging
import asyncio
from asyncio import Queue

from bitshares import BitShares
from bitshares.account import Account
from bitshares.market import Market
from bitshares.asset import Asset 
import sys 

from utils import *

class ManagerMeta(type):
    _coins = {}
    def __init__(cls, name, bases, dict):
        super(ManagerMeta, cls).__init__(name, bases, dict)
        cls.instance = None 

    def __call__(cls,*args,**kw):
        if cls.instance is None:
            cls.instance = super(ManagerMeta, cls).__call__(*args, **kw)
            ManagerMeta._devices[cls] = 1
        else:
            ManagerMeta._devices[cls] +=1  
        return cls.instance



class Manager:
    managers = {}

    def __init__(self, loop, logger,**kwargs):
        
        for key, item in kwargs.items():
            setattr(self, key, item)        
        self.logger = logging.getLogger("{}:{}".format(__name__, self.buy))
        
        if self.buy not in Manager.managers:
            Manager.managers[self.buy] = []
    
    @classmethod
    def from_worker(cls, w, loop, logger, **kwargs):
        #kwargs.update('buy' : )
        return cls(loop, logger, **kwargs)

    async def run(self):
        i = 0
        await asyncio.sleep(5)     
        
        while True:
            queues = Manager.managers[self.buy]
            for q in queues:
                try:
                    order = await q.get_nowait()
                    self.logger.info("received {}".format(order))
                except Exception as e:
                    pass
            await asyncio.sleep(0.5)


        
