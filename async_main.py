import os 
import time 
import asyncio
import logging 
import logging.config
import yaml

from async_Analyst import Analyst

if __name__ == '__main__':    
    
    buying = {'BRIDGE.BTC' : None, 'BRIDGE.LRM': None ,'BRIDGE.LCC' : None, 'BRIDGE.GIN' : None}
    data = {
        'pw' : "test",
        'acc' : "kipstar1337",
        'url' : 'wss://eu-west-2.bts.crypto-bridge.org',
        'major_coin' : 'BRIDGE.BTC',
        'buying' : {'BRIDGE.BTC' : None , 'BRIDGE.GIN': None}
    }

    with open('./logging.yml', 'r') as stream:
        config = yaml.load(stream)
        
    logging.config.dictConfig(config)
    loop = asyncio.get_event_loop()
    logger = logging.getLogger()
    ana = Analyst.from_kwargs(loop, logger, **data) 
    managers, workers = ana.populate()

    producer_coro = [w.run() for w in workers]
    consumer_coro = [m.run() for m in managers]
    #
    ana.loop.run_until_complete(asyncio.gather(*producer_coro, *consumer_coro))
    ana.loop.close()
    
    