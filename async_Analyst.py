import os 
import sys
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
import logging 




class Analyst:
    strategies = []

    def __init__(self,loop, logger, **kwargs):
        self.loop = loop
        
        self.logger = logger 
        
        for key, item in kwargs.items():
            setattr(self, key, item)
        self.update()
        self.logger.debug("Welcome !")
        
    def populate(self):
        workers = []
        buying = self.buying
        selling_coins = self.find_sellcoins(**buying)
        buying_coins  = self.find_buycoins(**buying)
        buying_coins.update(selling_coins)
        
        coins = buying_coins.keys()
        #[Manager(coin) for coin in buying_coins]

        for sell_coin in selling_coins:
            balance = selling_coins[sell_coin]
            self.logger.info("Owning {}".format(sell_coin))
            # Investment strategy
            if sell_coin != 'BRIDGE.BTC':
                tsize = balance
                th = 0.01 #asymmetric  th can be implemented here
                data = {
                    'sell' : sell_coin, 
                    'buy' : self.major_coin,
                    'tradingside' :'sell',
                    'tsize' : tsize, 
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
                    'state' : 0
                }

                w = Worker(self.loop, self.logger, **data)
                #await asyncio.sleep(1)
                time.sleep(1)
                workers.append(w)
            else:
                #equally distributed capital
                tsize = balance/len(buying_coins)
                th = 0.03 #always 5% spread
                self.logger.info("Investing btc {}".format(tsize))
                
                #NOTE:
                #since we use our full balance if we trade any other coin then btc
                # it is possible to fail an order due to insufficient balance
                
                for buy_coin in buying_coins:
                    # different markets
                    if buy_coin != sell_coin:
                        #init manager on market
                        # CheckSpread(tsize = tsize, th = th)
                        #m = Manager()
                        data = {
                            'sell' : self.major_coin, 
                            'buy' : buy_coin,
                            'tradingside':'buy',
                            'tsize' :tsize, 
                            'th' : th,
                            'ob_th' : 0.1,
                            'toQuote' : True,
                            'market_key' : "{}:{}".format(buy_coin, self.major_coin),
                            'instance' : self.instance,
                            'url' : self.url,
                            'acc' : self.acc,
                            'pw' : self.pw,
                            'orderbooklimit' : 25,
                            'open_order' : None,
                            'state' : 0
                        }
        
                        w = Worker(self.loop, self.logger, **data)
                        time.sleep(1)#await asyncio.sleep(1)
        
                        workers.append(w)
        #make manager
        managers = []
        m_d ={
            'buy' : None
        }
        for m in coins:
            #d = m_d.copy()
            #d['buy'] = m
            managers.append(Manager(self.loop, self.logger,  **data))
            #await asyncio.sleep(1)
            time.sleep(1)
        for m in managers:
            for w in workers:
                if w.tradingside == 'buy':
                    coin = w.buy
                else:
                    coin = w.sell
                if m.buy == coin:
                    Manager.managers[coin].append(w.queue)
        self.managers = managers
        self.workers = workers
        return managers, workers

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
        # # #
        buycoins = kwargs.copy()
        for coin, amount in self.balance.items():
            if coin in buycoins.keys():
                if coin == self.major_coin:
                    self.logger.info("Major balance: {}".format(amount))
                    self.major_balance = amount
                    del buycoins[coin]
                elif coin == "BTS":
                    self.logger.info("BTS amount {}".format(self.balance[coin]))
                else:
                    buycoins[coin] = self.balance[coin]
        return buycoins

    def find_sellcoins(self, **kwargs):
        # # #
        # kwargs: coins to sell besides major_coin 
        # 
        # # #
        try:
            return {'BRIDGE.BTC' : self.balance['BRIDGE.BTC']}#, 'BRIDGE.GIN' : self.balance['BRIDGE.GIN']}
        except Exception as e:
            raise ValueError('Couldnt assign balances, probably because orders are still open.', e)

    def step(self):
        #compute difference from one trading episode T = 5 minutes or smth..
        pass

    async def produce(self,w):
        #print("Starting producer.. {}".format(w))
        await w.run()
        
    async def consume(self,m,q):
        #print("Starting consumer.. {}".format(m))
        await m.run(q)
