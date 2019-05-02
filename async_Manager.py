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
        """
        kwargs:
            - 
        """
        for key, item in kwargs.items():
            setattr(self, key, item)        
        self.logger = logging.getLogger("{}:{}".format(__name__,self.buy))
        if self.buy not in Manager.managers:
            Manager.managers[self.buy] = []
        # 'amount_to_sell': {'amount': 30397, 'asset_id': '1.3.1570'},
        #  'min_to_receive': {'amount': 384474522, 'asset_id': '1.3.3543'}, 
        
        self.coin = Asset(self.buy)
        self.coin_orders = []

        if coin not in Manager.managers:
            Manager.managers[coin] = self
        
    def expired_or_not(self, order):
        #check if order is expired
        #for o in self.coin_orders:
        #    o.
        
        return True


    async def run(self):
        i = 0
        await asyncio.sleep(5)     
        while True:
            queues = Manager.managers[self.buy]
            for q in queues:
                try:
                    order = await q.get_nowait()
                    if self.expired_or_not(order):
                        self.logger.info("Order expired on market")
                    else:
                        self.logger.info("Order has been filled!")
                        #adjust balance    
                except Exception as e:
                    pass
            await asyncio.sleep(5)
            self.logger.info("new try in manager")


        
