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

class Analyst:
    strategies = []
    def __init__(self, **kwargs):
        #url = 'wss://eu-west-2.bts.crypto-bridge.org', major_coin = 'BRIDGE.BTC'):
        self.loop = asyncio.get_event_loop()

        for key, item in kwargs.items():
            setattr(self, key, item)

        self.update()
    
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
            print("     - {}".format(balance))
            # Investment strategy
            if sell_coin != 'BRIDGE.BTC':
                #use full balance
                #NOTE: is this correct?
                tsize = balance
                th = 0.01 #asymmetric  th can be implemented here
                data = {
                    'sell' : sell_coin, 
                    'buy' : self.major_coin,
                    'tradingside' :'sell',
                    'tsize' : tsize, 
                    'th' : th,
                    'toQuote' : False,
                    'market_key' : "{}:{}".format(sell_coin, self.major_coin),
                    'instance' : self.instance,
                    'url' : self.url,
                    'acc' : self.acc,
                    'pw' : self.pw,
                    'orderbooklimit' : 25,
                    'open_order' : None
                }

                w = Worker.from_kwargs(self.loop,**data)
                time.sleep(1)
                workers.append(w)
            else:
                #equally distributed capital
                tsize = balance/len(buying_coins)
                th = 0.05 #always 5% spread

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
                            'toQuote' : True,
                            'market_key' : "{}:{}".format(buy_coin, self.major_coin),
                            'instance' : self.instance,
                            'url' : self.url,
                            'acc' : self.acc,
                            'pw' : self.pw,
                            'orderbooklimit' : 25,
                            'open_order' : None
                        }
                        

                        w = Worker.from_kwargs(self.loop,**data)
                        time.sleep(1)
                
                        workers.append(w)

        managers = []
        m_d ={
            'buy' : None
        }
        for m in coins:
            d = m_d.copy()
            d['buy'] = m
            managers.append(Manager(self.loop, **d))

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
    def from_kwargs(cls, **kwargs):
        instance = BitShares(witness_url = kwargs['url'])
        account = Account(kwargs['acc'], bitshares_instance = instance, full = True)
        account.bitshares.wallet.unlock(kwargs['pw'])
        kwargs.update({'account' : account, 'instance': 'instance'})
        print(kwargs)
        return cls(**kwargs)

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

    def step(self):
        #compute difference from one trading episode T = 5 minutes or smth..
        pass

    async def produce(self,w):
        print("Starting producer.. {}".format(w))
        await w.run()
        
    async def consume(self,m,q):
        print("Starting consumer.. {}".format(m))
        await m.run(q)
"""

    def cancel_all_orders(self, market_key, order_list = None):
        
        So far this function cancels all orders for a specific market.
        However, it is desirable to manually pass a list of orderids that are supposed to be cancelled.
        This is currently under construction as we also need to manually pass the markets OR retrieve them
        via their asset id from the order
        if not order_list:

            # Create list of orders to be cancelled, depending on a specific market
            # TODO we are actually signing up twice in the same market because get_market_open_orders requires a market too
            market = self.get_market(market_key)
            orders = self.open_orders
            print((len(orders), 'open orders to cancel'))
            if len(orders):
                attempt = 1
                order_list = []
                for order in orders:
                    order_list.append(order['id'])

            while attempt:
                try:
                    details = market.cancel(order_list, account  = self.account)
                    print(details)
                    attempt = 0
                    return True
                except:
                    print((attempt, 'cancel failed', order_list))
                    attempt += 1
                    if attempt > 3:
                        print('cancel aborted')
                        return False
                    pass



"""