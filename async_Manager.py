import json
import time 
import pandas as pd
import numpy as np
import sys
import asyncio

from bitshares import BitShares
from bitshares.account import Account
from bitshares.market import Market

from Strategy import MarketStrategy, CheckSpread
from utils import *

class Manager:
    
    def __init__(self, buy, sell, account, strategy = None,url = 'wss://eu-west-2.bts.crypto-bridge.org'):
        #
        self.history = []
        self.buy  = buy 
        self.sell = sell
        #
        self.market_key = '{}:{}'.format(buy, sell)
        self.strategy = strategy
        #
        self.pw = "5KgkgfK4suQqLJY1Uv8mY4tPx4e8V8a2q2SX8xbS5o8UN9rxBJJ"
        self.acc = "kipstar1337"
        self.account = account
        self.account.refresh()
        #
        self.open_order = None 
        self.trades = {} 
        #Ordereddict with timestamp or dataframe is smart le 
        self.workers = []
        self.listening = []
        
    async def balance(self):
        self.account.refresh()
        my_coins = self.account.balances
        return dict(zip(map(lambda x: getattr(x,'symbol'),my_coins),my_coins))
    
    @property
    async def open_orders(self):
        self.account.refresh()
        open_orders = self.account.openorders
        return open_orders

    async def run(self):
        print("Starting to run on {}".format(self.market_key))
        i = 0
        assert(self.strategy)
        assert(self.q)
        q = self.q
        await asyncio.sleep(5)     
        while True:
            #await asyncio.sleep(2) 
            i += 1            
            current_state = self.strategy.state
            entry = await q.get()
            orders = await self.open_orders
            #print("R".format(self.market_key))
            task = self.strategy.apply(entry)
            if(task):
                print("Now we need to implement a pipe to analyst which deals with the task returned by strategy")
            if i%5 == 0:
                print("Buying: {} Selling: {} , in state {} after {} iteratios".format(self.buy, self.sell, self.state, i))
                #print("{}:{} is in state {} after {} iterations".format(self.market_key, current_state, i)) 
                if len(orders):
                    print("OpenOrders in {}".format(self.market_key))
                    for order in orders:
                        print("{}: {}".format(self.market_key, order))
                else:
                    print("No open orders")


                print(" -------------------------------------------")
            await asyncio.sleep(1)


        
