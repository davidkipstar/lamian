import os 
import time 
import asyncio

from async_Manager import Manager
from async_Worker import Worker
from Strategy import CheckSpread
#from utils import convert_to_quote
from copy import deepcopy
from async_Analyst import Analyst
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

if __name__ == '__main__':
    
    ana = Analyst() 
    managers = {} # 
    buying = {'BRIDGE.BTC' : None, 'BRIDGE.LGS': None ,'BRIDGE.LCC' : None, 'BRIDGE.GIN' : None}
    #selling are all coins we have a balance

    i = 0 # i  
    while ana.major_balance > 0:
          
        #Start Asyncio
        loop = asyncio.get_event_loop()
        #
        i += 1
        #coins to trade
        selling_coins = ana.find_sellcoins(**buying)
        buying_coins  = ana.find_buycoins(**buying)
        
        print("We are in loop {} owning ...".format(i))
        #Init Manager on market sell-buy for  
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
                    'sell' : ana.major_coin, 
                    'buy' : buy_coin,
                    'tradingside'='sell',
                    'tsize' =tsize, 
                    'th' = th
                    'toQuote' : False,
                    'loop' : loop
                }

                m = Manager(**data)
            
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
                            'sell' : ana.major_coin, 
                            'buy' : buy_coin,
                            'tradingside'='buy',
                            'tsize' =tsize, 
                            'th' = th,
                            'toQuote' : True,
                            'loop' : loop
                        }
                        m = Manager(**data)
                      
        workers = []
        workers_dict = Manager.populate(loop)
        for key, _workers in workers_dict.items():
            print("Manager {} managing {} workers".format(key, len(_workers)))
            for w in _workers:
                workers.append(w)
                
        producer_coro = [w.run() for w in workers]
        consumer_coro = [m.run() for m in managers.values()]
        #
        loop.run_until_complete(asyncio.gather(*producer_coro, *consumer_coro, ana.run()))
        loop.close()
        #
        ana.update()




    """
        #Init Workers and queues
        trading_markets = {}        
        
        def mirror_key(key):
            m_key = key.split(':')
            m_key.reverse()
            return ':'.join(m_key)
        
        print("Using Async, populating worker with queues")
        for key, manager in managers.items():

            #check if buy:sell exists as sell:buy
            queue = asyncio.Queue(loop=loop)
            #insert to maanger
            manager.q = queue
            if key in trading_markets: 
                #market already exists
                trading_markets[key].append(queue)
                #trading_markets[key] = asyncio.Queue(loop=loop)
            elif mirror_key(key) in trading_markets:
                #trading_markets[mirror_key(key)] = asyncio.Queue(loop=loop) 
                trading_markets[mirror_key].append(queue)
            else:
                trading_markets[key] = [queue]
        for key, items in trading_markets.items():
            #for item in items:
            w = Worker.from_manager(manager, ana.instance, queues = items ,market_key = key,**w_config)
            workers.update({ w.id : w })
        """
