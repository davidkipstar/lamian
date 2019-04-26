import json
import time 
import pandas as pd
import numpy as np
import sys
import asyncio
from asyncio import Queue

from bitshares import BitShares
from bitshares.account import Account
from bitshares.market import Market

from async_Analyst import Analyst
from Strategy import MarketStrategy, CheckSpread
from utils import *

class Manager(Analyst):
    
    managers = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
   # sell, buy, account, tradingside = 'buy' ,strategy = None, toQuote = True,url = 'wss://eu-west-2.bts.crypto-bridge.org'):
        #
        data = {
            'open_orders' : None,
            'trades' : {}}
        for key, item in kwargs.items():
            setattr(self, key, item)
        
        if tradingside == 'buy':
            self.quote = buy
            self.base = sell
        else:
            self.quote = sell
            self.base = buy
        
        self.workers = []
        self.w_config = {'orderbooklimit' : 25,
                    'open_order' : None,
                    'max_open_orders' : 1,
                    'state' : None,
                    'arbitrage' : False
                    }
        self.w_config = self.w_config.update(**kwargs)
                

        self.listening = []
        
    @staticmethod
    def populate(loop):
        #
        q = {}
        for key, manager in Manager.managers.items():
            q[manager.id] = []
            for i in range(manager.worker_count):
                #unterscheiden zwischen orderbook und user
                queue = Queue(loop=loop)
                w = Worker.from_manager(m, queue,**m.w_config)
                q[manager.id].append(w)
        return q
    
    async def balance(self):
        self.account.refresh()
        my_coins = self.account.balances
        return dict(zip(map(lambda x: getattr(x,'symbol'),my_coins),my_coins))
    
    @property
    async def open_orders(self):
        self.account.refresh()
        open_orders = self.account.openorders
        return open_orders

    async def run(self, **kwargs):
        i = 0

        await asyncio.sleep(5)     
        while True:
            #await asyncio.sleep(2) 
            entry = await q.get()
            print("Manager", entry)
            await asyncio.sleep(1)


        
