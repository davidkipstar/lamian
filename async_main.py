import os 
import time 
import asyncio

from async_Manager import Manager
from async_Worker import Worker

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

    def __init__(self, url = 'wss://eu-west-2.bts.crypto-bridge.org', major_coin = 'BRIDGE.BTC'):
        
        self.instance = BitShares(witness_url = url)
        self.pw = "5KgkgfK4suQqLJY1Uv8mY4tPx4e8V8a2q2SX8xbS5o8UN9rxBJJ"
        self.acc = "kipstar1337"
        self.major_coin = major_coin
        account = Account(self.acc, bitshares_instance = self.instance, full = True)
        account.bitshares.wallet.unlock(self.pw)
        self.account = account
        print("Manager: Account unlocked: {}".format(account.bitshares.wallet.unlocked()))
        #get balance
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

    def step(self):
        #compute difference from one trading episode T = 5 minutes or smth..
        pass

    async def produce(self,w):
        print("Starting producer.. {}".format(w))
        await w.run()
        
    async def consume(self,m,q):
        print("Starting consumer.. {}".format(m))
        await m.run(q)
        
async def main(ana,q):
    
    producers = [asyncio.create_task(ana.produce(w)) for w in workers.values()]
    consumers = [asyncio.create_task(ana.consume(m,q )) for m in managers.values()]
    await asyncio.gather(*producers)
    #for m in managers.values():
    await q.join()  # Implicitly awaits consumers, too
    print("Canceling all consumers")
    for c in consumers:
        c.cancel()

    print("Sleeping for 10 seconds...")
    for i in range(5):
        print(".")
        time.sleep(2)


if __name__ == '__main__':
    
    ana = Analyst() 
    managers = {}
    workers = {}
    #major_coin = BTC
    q = asyncio.Queue()
    while ana.major_balance > 0:

        buying = {'BRIDGE.BTC' : None, 'BRIDGE.LCC' : None, 'BRIDGE.GIN' : None}
        selling_coins = ana.find_sellcoins(**buying)
        buying_coins  = ana.find_buycoins(**buying)

        print("Selling coins : {}".format(selling_coins))
        print("Buying coins  : {}".format(buying_coins))
        

        for sell_coin in selling_coins:
            for buy_coin in buying_coins:
                if buy_coin != sell_coin:
                    m = Manager(sell_coin, buy_coin, ana.account, q)
                    managers.update({ m.name : m })        
        
        for manager in managers.values():
            w = Worker.from_manager(manager, ana.instance,**w_config)
            workers.update({ w.name: w })
        #
        loop = asyncio.get_event_loop()
        queue = asyncio.Queue(loop=loop)
        producer_coro = [w.run(queue) for w in workers.values()]
        consumer_coro = [m.run(queue) for m in managers.values()]
        loop.run_until_complete(asyncio.gather(*producer_coro, *consumer_coro))
        loop.close()

    #ana.step()
    #to here

