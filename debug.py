# -*- coding: utf-8 -*-
"""
Created on Wed Feb 20 11:10:45 2019

@author: winju
"""
#import json
#import os
#
#os.chdir('C:\\Users\\winju\\rep\\lamian')
#
#f = open('standard-settings.json')
#j = json.load(f)
#for key, value in j.items():
#    print(key, value)
#    
#    
#    
#    setattr(self, key, value)
#    setattr(self, 'basecur', base)
#    setattr(self, 'quotecur', quote)
#
#
#
#
#def settings(self, filename):
#        # pose boundary on settings here if wanted
#        print('Filename : {}'.format(filename))
#        base, quote = filename.split(':')
#        with open('standard-settings.json') as f:
#            j = json.load(f)
#            for key, value in j.items():
#                setattr(self, key, value)
#        setattr(self, 'basecur', base)
#        setattr(self, 'quotecur', quote)
#        
#        
import os 
import time 

from utils import *

from worker import Worker
from manager import Manager

if __name__ == '__main__':

    #setup 
    m = Manager('credentials.json')
    m.signup()
    m.initial_balance()

    sellcoins = m.pick_sellcoins()
    print(sellcoins)
    #sell_markets = [
    
    # 
#    for coin in sellcoins.values():
#        market = 'BRIDGE.BTC:BRIDGE.'+ getattr(coin,'symbol')
#        print(market)
        #m.add_worker(market, sellcoins[coin.symbol].amount - 0.00001, btc=False)

    btcbalance = m.balances['BRIDGE.BTC']

    buycoins = ['LCC', 'LPC']
    for coin in buycoins:
        
        try:
            # Check if we actually have this coin
            m.balances['BRIDGE.{}'.format(coin)]
        except Exception as e:
            continue;
        
        # 
        market = 'BRIDGE.{}:BRIDGE.BTC'.format(coin)
        print(market)
        tsize = 0.001

        m.add_worker(market, tsize)
        #check if true
        btcbalance = btcbalance - tsize
        time.sleep(1)
  
        
for currency, workers in m.currencies.items():
            for worker in workers:
                worker.state = None
                p = Process(target=Worker.run,args=(worker,))
                p.daemon = True
                print(p)
                #p.start()