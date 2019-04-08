import os 
import time 
import asyncio

from async_Manager import Manager
from async_Worker import Worker
from Strategy import CheckSpread

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
        
if __name__ == '__main__':
    
    ana = Analyst() 
    managers = {} # keys: SELL_COIN:BUY_COIN
    workers = {}
    buying = {'BRIDGE.BTC' : None, 'BRIDGE.LCC' : None, 'BRIDGE.GIN' : None}
    
    i = 0 
    while ana.major_balance > 0:
        i += 1
        #Get Coins to trade
        selling_coins = ana.find_sellcoins(**buying)
        buying_coins  = ana.find_buycoins(**buying)
        print("Starting ... loop {}".format(i))
        #Init Manager on market sell-buy for  
        for sell_coin in selling_coins:
            balance = selling_coins[sell_coin]
            print("Owning {} of {}".format(balance, sell_coin))

            #NOTE:
            # This can be replaced by an investment strategy
            if sell_coin != 'BRIDGE.BTC':
                #use full balance
                tsize = balance
                th = 0.01 #asymmetric  th can be implemented here

            else:
                #equally distributed capital
                tsize = balance/len(buying_coins)
                th = 0.05 #always 5% spread
            ## 
            
            #NOTE:
            #since we use our full balance if we trade any other coin then btc
            # it is possible to fail an order due to insufficient balance
            for buy_coin in buying_coins:
                if buy_coin != sell_coin:
                    #init manager on market
                    strategy = CheckSpread(tsize = tsize, th = 0.05)
                    m = Manager(sell_coin, buy_coin, ana.account, strategy = strategy)
                    managers.update({"{}:{}".format(sell_coin, buy_coin) : m })
        

        #Start Asyncio
        loop = asyncio.get_event_loop()
        
        #Init Workers and queues
        trading_markets = {}
        
        
        def mirror_key(key):
            m_key = key.split(':')
            m_key.reverse()
            return ':'.join(m_key)
        
        print("Create asyncio")
        for key, manager in managers.items():
            #check if buy:sell exists as sell:buy
            
            if key in trading_markets: 
                #market already exists
                #trading_markets[key].append(asyncio.Queue(loop=loop))
                trading_markets[key] = asyncio.Queue(loop=loop)
            elif mirror_key(key) in trading_markets:
                trading_markets[mirror_key(key)] = asyncio.Queue(loop=loop) 
                #trading_markets[mirror_key].append(asyncio.Queue(loop=loop))
            else:
                trading_markets[key] = asyncio.Queue(loop=loop)
            print("Key: {}".format(key))
            w = Worker.from_manager(manager, ana.instance, market_key = key,**w_config)
            workers.update({ w.id : w })
        
        print("Transition table...")
        #create transition table for queues
        for key, queue in trading_markets.items():
            print("Transition from {}".format(key))
            for worker in workers.values():
                #
                if key == worker.market_key or mirror_key(key) == worker.market_key:
                    worker.q = queue

                    print("........ {}".format(worker.market_key))
            
            if key in managers:
                m = managers[key]
                m.q = queue
            elif mirror_key(key) in managers:
                m = managers[mirror_key(key)]
                m.q = queue
            else:
                print("{} not found in managers... ".format(key))
        #check if populated
        for w in workers.values():
            print(w.q)

        producer_coro = [w.run() for w in workers.values() ]
        consumer_coro = [m.run() for m in managers.values()]
        #
        loop.run_until_complete(asyncio.gather(*producer_coro, *consumer_coro))
        loop.close()
        #
        ana.update()



