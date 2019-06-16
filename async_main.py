import os 
import time 
import asyncio
import logging 
import logging.config
import yaml
import json
from async_Analyst import Analyst

if __name__ == '__main__':    
    
    with open('credentials.json') as f:
        j = json.load(f)

    data = {
        'pw' : j['pw'],
        'acc' : j['acc'],
        'url' : 'wss://eu-west-2.bts.crypto-bridge.org',
        'major_coin' : 'BRIDGE.BTC',
        'whitelist' : ['BRIDGE.GIN', 'BRIDGE.ZNN', 'BRIDGE.SINS', 'BRIDGE.XGA', 'BRIDGE.ONEX', 'BRIDGE.HISC'],
        'blacklist' : ['BRIDGE.BTS'],
    }

    #logging
    with open('./logging.yml', 'r') as stream:
        config = yaml.load(stream)
    
    #logging.config.dictConfig(config)
    logging.basicConfig(format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        filename='logs.log',
                        level=logging.WARNING) # info else
    
    #async
    loop = asyncio.get_event_loop()
    logger = logging.getLogger()
    logger.propagate = False
    ana = Analyst.from_kwargs(loop, logger, **data)
    managers, workers = ana.populate()

    producer_coro = [w.run() for w in workers]
    consumer_coro = [m.run() for m in managers]
    
    ana.loop.run_until_complete(asyncio.gather(*producer_coro, *consumer_coro))
    ana.loop.close()