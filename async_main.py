import os 
import time 
import asyncio
from async_Manager import Manager
from async_Worker import Worker
from Strategy import CheckSpread
from async_Analyst import Analyst


async def run(producer_coro,consumer_coro,**kwargs):
    #
    producer_coro.extend(consumer_coro)
    await asyncio.gather(*producer_coro, *consumer_coro, **kwargs)
    
if __name__ == '__main__':
    
    buying = {'BRIDGE.BTC' : None, 'BRIDGE.LGS': None ,'BRIDGE.LCC' : None, 'BRIDGE.GIN' : None}
    #selling are all coins we have a balance
    data = {
        'pw' : "5KgkgfK4suQqLJY1Uv8mY4tPx4e8V8a2q2SX8xbS5o8UN9rxBJJ",
        'acc' : "kipstar1337",
        'url' : 'wss://eu-west-2.bts.crypto-bridge.org',
        'major_coin' : 'BRIDGE.BTC',
        'buying' : {'BRIDGE.BTC' : None , 'BRIDGE.LGS': None , 'BRIDGE.GIN': None}
    }

    ana = Analyst.from_kwargs(**data) 
    #
    asyncio.run(run(*ana.populate()))#, loop = ana.loop))
    #ana.loop.close(


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
