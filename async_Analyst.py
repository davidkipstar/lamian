import os 
import sys
import time 
import asyncio

from Manager import Manager
from Worker import Worker
from Strategy import CheckSpread
#from utils import convert_to_quote
from copy import deepcopy

from bitshares import BitShares
from bitshares.account import Account
from bitshares.market import Market
import logging 

from decimal import Decimal


class Analyst:
    strategies = []
    satoshi = Decimal('0.00000001')
    def __init__(self,loop, logger, **kwargs):
        #
        self.loop = loop
        self.logger = logger 
        
        for key, item in kwargs.items():
            setattr(self, key, item)
    
        self.account = Account(self.acc)
        self.account.refresh()
        my_coins = self.account.balances
        self.update()
        self.logger.info("Major Coin: {}".format(self.major_coin))
        self.logger.info("Major Balance: {}".format(self.major_balance))
        self.logger.info("Welcome !")
        self.connections = {}
        
    
    def connect(self, m, worker):
        """ 
        Connect:
            Tasks:
                if worker not connected with manager, connect
        """

        Manager.managers[m.coin].append(worker.queue)

    def generate_data(self, coin, amount, **kwargs):
        """
        ADJUST THIS SHIT HERE
        data = {
                    'sell' : sell_coin, 
                    'buy' : self.major_coin,
                    'tradingside' :'sell',
                    'tsize' : 0 if tsize <= 0.01 else tsize, 
                    'th' : th,
                    'ob_th' : 0.1,
                    'toQuote' : False,
                    'market_key' : "{}:{}".format(sell_coin, self.major_coin),
                    'instance' : self.instance,
                    'url' : self.url,
                    'acc' : self.acc,
                    'pw' : self.pw,
                    'orderbooklimit' : 25,
                    'open_order' : None,
                    'state' : 0,
                    'major_coin' : sell_coin
                }
        """
        data = {'major_coin' : 'BRIDGE.BTC',
                    'instance' : self.instance,
                    'url' : self.url,
                    'acc' : self.acc,
                    'pw' : self.pw,
                    'orderbooklimit' : 25,
                    'open_order' : None,
                    'state' : 2,
                    'ob_th' : 0.1}
        if kwargs['tradingside'] == 'buy':
            data['buy'] = coin 
            data['sell'] = self.major_coin
            data['tsize'] = (0.5 * self.major_balance['amount'])/len(self.whitelist) # only invest half of our btc at a time
            data['th'] = 0.03
            data['ob_th'] = 1

        if kwargs['tradingside'] == 'sell':
            data['sell'] = coin 
            data['buy'] = self.major_coin
            data['th'] = 0.0025
            data['tsize'] = 0
            data['state'] = 2
            data['ob_th'] = 1

        kwargs.update(data)
        return kwargs
    
    def populate(self):
        """
        Populate:
            Tasks:
                - filter whitelist, blacklist, bts 
                - initialize worker 
        """
        ## WORKER
        self.worker_data = {} # insert all used kwrags dictionary here!!!!!!!!!!!!!!!!!
        workers = []
        #sellcoins 
        selling_coins = self.find_sellcoins()
        for coin, amount in selling_coins.items():
            self.logger.info("Selling {} owning {}".format(coin, amount))
            data = self.generate_data(coin, amount, tradingside = 'sell')
            self.worker_data["{}:{}".format(coin, self.major_coin, **data)] = data.copy() #different
            workers.append(Worker.from_kwargs(self.loop, self.logger, **data))
            time.sleep(1)
            #generate data

        #data['tradingside'] = 'buy'
        buying_coins  = self.find_buycoins()
        for coin, amount in buying_coins.items():
            self.logger.info("Buying {} owning {}".format(coin, amount))
            data = self.generate_data(coin, amount, tradingside = 'buy')
            self.worker_data["{}:{}".format(self.major_coin, coin)] = data.copy()
            workers.append(Worker.from_kwargs(self.loop, self.logger,**data))
            time.sleep(1)

        ## MANAGER
        ms = []
        for w in workers:
            ms.append(Manager(self.loop, self.logger, coin = w.market_key.split(':')[0]))     
            time.sleep(1)

        ## BUILD GRAPH
        for m in ms:
            for w in workers:
                self.connect(m, w)
        return ms, workers                
    async def run(self):
        print("run")
            

    @classmethod
    def from_kwargs(cls,loop, logger, **kwargs):
        instance = BitShares(witness_url = kwargs['url'])
        account = Account(kwargs['acc'], bitshares_instance = instance, full = True)
        account.bitshares.wallet.unlock(kwargs['pw'])
        kwargs.update({'account' : account, 'instance': 'instance'})
        return cls(loop,logger, **kwargs)

    def update(self):
        self.account.refresh()
        my_coins = self.account.balances
        self.balance = dict(zip(map(lambda x: getattr(x,'symbol'),my_coins),my_coins))
        self.major_balance = self.balance[self.major_coin]
        

    def find_buycoins(self, **kwargs):
        # # # 
        # kwargs: coins allowed to buy
        # get balances and check if it is allowed coin
        # #
        buycoins = {}
        investing_tsize = self.major_balance/len(self.whitelist)
        for coin in self.whitelist:
            buycoins[coin] = investing_tsize #is in BTC
        return buycoins

    def find_sellcoins(self, **kwargs):
        # # #
        # filter 
        # # #
        sellcoins = {}
        for coin in self.whitelist:
            if coin in self.balance and coin != self.major_coin:
                sellcoins[coin] = self.balance[coin]
        return sellcoins 

    def step(self):
        #compute difference from one trading episode T = 5 minutes or smth..
        pass

    async def produce(self,w):
        #print("Starting producer.. {}".format(w))
        await w.run()
        
    async def consume(self,m,q):
        #print("Starting consumer.. {}".format(m))
        await m.run(q)
