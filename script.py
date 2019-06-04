#This script is written to fetch orderbooks async from markets 

import pandas as pd 

from bitshares import BitShares
from bitshares.account import Account
from bitshares.market import Market
from datetime import datetime
from json import dumps

from utils import json_serial

import time 
from pathlib import Path

from tinydb import Query, TinyDB
import time 
import asyncio 
db = TinyDB('mydata.json')
#db.insert({'market': 'BRIDGE.BTC:BRIDGE.LGS', 'timestamp' : time.time() ,'asks' : {}})
#usr = Query()
#print(db.search(usr.market == 'BRIDGE.BTC:BRIDGE.LGS'))
#variables
orderbook_limit = 25
market1 = 'BRIDGE.BTC:BRIDGE.GIN'
market2 = 'BRIDGE.BTC:BRIDGE.LGS'
market3 = 'BRIDGE.BTC:BRIDGE.LCC'

markets = [market1, market2, market3]

class Margret:
    def __init__(self, market_key):
        self.pw = "5KgkgfK4suQqLJY1Uv8mY4tPx4e8V8a2q2SX8xbS5o8UN9rxBJJ"
        self.acc = "kipstar1337"
        self.instance = BitShares()
        self.market_key = market_key
        self.market =  Market(market_key, block_instance = self.instance)
        self.market.bitshares.wallet.unlock(self.pw)

    #async
    async def run(self, minutes):
        start = time.time()
        delta = 30
        time_now = time.time()
        last_update = time.time()
        counter = 0 

        while start + minutes*60 > time_now: 
            time_now = time.time()
            if time_now - last_update > delta:
                last_update = time.time()
                orderbook = self.market.orderbook(orderbook_limit ) # 
                counter = counter + 1
                db.insert({
                    'timestamp' : dumps(datetime.now(), default=json_serial),
                    'market' : self.market_key,
                    'orderbook' : orderbook 
                })
            print("Added orderbook from market {}".format(self.market_key))
            await asyncio.sleep(5)
#print dumps(datetime.now(), default=json_serial)

if __name__ == '__main__':
    tasks = []
    for market in markets:
        tasks.append(Margret(market))
    #
    loop = asyncio.get_event_loop()
    async_tasks = asyncio.gather(*[task.run(5) for task in tasks])
    loop.run_until_complete(async_tasks)
