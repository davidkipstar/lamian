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
    
    def __init__(self, buy, sell, account, url = 'wss://eu-west-2.bts.crypto-bridge.org'):
        self.arbitrage = 0
        self.history = []
        self.buy  = buy 
        self.sell = sell
        self.market_key = '{}:{}'.format(buy, sell)
        self.strategy = CheckSpread()
        #
        self.pw = "5KgkgfK4suQqLJY1Uv8mY4tPx4e8V8a2q2SX8xbS5o8UN9rxBJJ"
        self.acc = "kipstar1337"
        self.account = account
        self.account.refresh()
        self.open_order = None 
        self.trades = {} #Ordereddict with timestamp or dataframe is smart le 
        self.workers = []
        self.listening = []
        
    def balance(self):
        self.account.refresh()
        my_coins = self.account.balances
        return dict(zip(map(lambda x: getattr(x,'symbol'),my_coins),my_coins))
    
    @property
    def open_orders(self):
        self.account.refresh()
        open_orders = self.account.openorders
        return open_orders

    async def run(self, q):
        #
        print("Starting to run on {}".format(self.market_key))
        i = 0
        await asyncio.sleep(5)     
        while True:
            #await asyncio.sleep(2) 
            i += 1            
            current_state = self.strategy.state
            entry = await q.get()
            orders = self.open_orders
            print("Entry on  {}".format(self.market_key))
            if i%5 == 0:
                print("{} is in state {} after {} iterations".format(self.market_key, current_state, i)) 
                if len(orders):
                    print("OpenOrders in {}".format(self.market_key))
                    for order in orders:
                        print("{}: {}".format(self.market_key, order))
                print(" -------------------------------------------")
            await asyncio.sleep(1)
            """
            print("Manager {}".format(self.name))
            await asyncio.sleep(3)
            j = await q.get()
            #global 
            print("{} received {}".format(self.name, j))
            #self.strategy.apply(j)
            q.task_done()
            """


        
