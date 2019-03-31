import json
import time 
import pandas as pd
import numpy as np
import sys
import asyncio

from bitshares import BitShares
from bitshares.account import Account
from bitshares.market import Market

from Strategy import MarketStrategy

from utils import *


class Manager:
    
    def __init__(self, buy, sell, account, q, 
            url = 'wss://eu-west-2.bts.crypto-bridge.org'):
        
        self.arbitrage = 0
        self.history = []
        self.q = q#asyncio.Queue()

        self.buy  = buy 
        self.sell = sell
        self.name = '{}:{}'.format(buy, sell)

        self.strategy = MarketStrategy()

        self.pw = "5KgkgfK4suQqLJY1Uv8mY4tPx4e8V8a2q2SX8xbS5o8UN9rxBJJ"
        self.acc = "kipstar1337"
        
        self.account = account
        self.account.refresh()

        self.open_order = None 
        self.trades = {} #Ordereddict with timestamp or dataframe is smart le 
        self.workers = []
        
    def balance(self):
        self.account.refresh()
        my_coins = self.account.balances
        return dict(zip(map(lambda x: getattr(x,'symbol'),my_coins),my_coins))
    

    async def run(self, q):
        #
        while True:
            print("Manager {}".format(self.name))
            await asyncio.sleep(3)
            j = await q.get()
            #global 
            print("{} received {}".format(self.name, j))
            #self.strategy.apply(j)
            q.task_done()
            

        
