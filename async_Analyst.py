import os 
import time 
import asyncio

from async_Manager import Manager
from async_Worker import Worker
from Strategy import CheckSpread
#from utils import convert_to_quote
from copy import deepcopy

from bitshares import BitShares
from bitshares.account import Account
from bitshares.market import Market

global managers #this is in Analyst
global workers  #this is in Analyst

w_config = {'orderbooklimit' : 25,
            'tradingside' : 'buy',
            'open_order' : None,
            'tsize' : 0.000000001,
            'th' : 0.05,
            'max_open_orders' : 1,
            'price_bid' : None ,
            'state' : None,
            'history' : [],
            'arbitrage' : False}

m_config = {}


class Analyst:

    def __init__(self, **kwargs)#url = 'wss://eu-west-2.bts.crypto-bridge.org', major_coin = 'BRIDGE.BTC'):
        
        data = {
            'pw' = "5KgkgfK4suQqLJY1Uv8mY4tPx4e8V8a2q2SX8xbS5o8UN9rxBJJ",
            'acc' = "kipstar1337",
            'url' = 'wss://eu-west-2.bts.crypto-bridge.org',
            'major_coin' = 'BRIDGE.BTC'
        }
        
        for key, item in kwargs.items():
            setattr(self, key, item)

        self.instance = BitShares(witness_url = url)
                
        account = Account(self.acc, bitshares_instance = self.instance, full = True)
        account.bitshares.wallet.unlock(self.pw)
        kwargs.update({'account' : account})
        self.account = account
        print("Manager: Account unlocked: {}".format(account.bitshares.wallet.unlocked()))
        self.update()

    def update(self):
        self.account.refresh()
        my_coins = self.account.balances
        self.balance = dict(zip(map(lambda x: getattr(x,'symbol'),my_coins),my_coins))
        self.major_balance = self.balance[self.major_coin]
        if self.major_balance:
            print("Owing {} of {}".format(self.major_balance, self.major_coin))


    def find_buycoins(self, **kwargs):
        # # # 
        # kwargs: coins allowed to buy
        # get balances and check if it is allowed coin
        # # #
        buycoins = kwargs.copy()
        for coin, amount in self.balance.items():
            if coin in buycoins.keys():
                if coin == self.major_coin:
                    print("Major coin balance: {}".format(amount))
                    self.major_balance = amount
                    del buycoins[coin]
                elif coin == "BTS":
                    print("BTS amount {}".format(self.balance[coin]))
                else:
                    print("Already owning {} of {}".format(amount, coin))
                    buycoins[coin] = self.balance[coin]
        return buycoins

    def find_sellcoins(self, **kwargs):
        # # #
        # kwargs: coins to sell besides major_coin 
        # 
        # # #
        return {'BRIDGE.BTC' : self.balance['BRIDGE.BTC']}

    def find_strategy(self, tradingside, tsize, th):
        #compute tsize
        return CheckSpread(tradingside, tsize = tsize, th = th)

    def step(self):
        #compute difference from one trading episode T = 5 minutes or smth..
        pass

    async def produce(self,w):
        print("Starting producer.. {}".format(w))
        await w.run()
        
    async def consume(self,m,q):
        print("Starting consumer.. {}".format(m))
        await m.run(q)
        