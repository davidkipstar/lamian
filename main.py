import os 
import time 

os.chdir('/home/julian/prg/lamian')

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
    #allowed_sellcoins =  ['LRM', 'LGS']
    
    for coin in sellcoins.values():

        market = 'BRIDGE.BTC:'+ getattr(coin,'symbol')
        print(market)
        m.add_worker(market, sellcoins[coin.symbol].amount - 0.00001, btc=False)



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
        tsize = 0.01

        m.add_worker(market, tsize)
        #check if true
        btcbalance = btcbalance - tsize
        time.sleep(1)

    
    """
    buycoins = ['XMR','LCC','BCO','XRP']
    for coin in buycoins:
        market = 'BRIDGE.{}:BRIDGE.BTC'.format(coin)
        tsize = 0.0000001

    buycoins = ['LRM', 'LPC']
    for coin in buycoins:
        market = 'BRIDGE.{}:BRIDGE.BTC'.format(coin)
        tsize = 0.001

        m.add_worker(market, tsize)
        #check if true
        btcbalance = btcbalance - tsize
"""

    
m.start()

while m.listen():
    #
    x = m.q.get()
    print(x)

    
