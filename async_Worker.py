import json
import time 
import pandas as pd
import sys

from bitshares import BitShares
from bitshares.account import Account
from bitshares.market import Market

from utils import *

from Strategy import CheckSpread
from async_Manager import Manager


class Worker(Manager):

    def __init__(self, market, tsize, th = 0.05,btc=True):
        print("---- init worker on {} -----".format(market))       
        with open('credentials.json') as f:
            d = json.load(f)
        
        url = 'wss://eu-west-2.bts.crypto-bridge.org'
        instance = BitShares(witness_url = url)
        account = Account(d['acc'], bitshares_instance = instance)
        account.bitshares.wallet.unlock(d['pw'])
        
        print("Worker: unlocked is {}".format(account.bitshares.wallet.unlocked()))
        super().__init__(account)
        
        if type(market) == str: 
            base, quote = market.split(':')    
        setattr(self, 'basecur', base)
        setattr(self, 'quotecur', quote)

        self.orderbooklimit = 25
        self.price_bid = None 
        self.orders = []
        self.state = None
        self.strategy = CheckSpread(tsize=tsize,th=th)
        self.market_string = market
        self.max_open_orders = 1
        
        # Below: Depends on Manager input
        self.keep_buying = None
        self.do_cancel = None
        self.amount_open_orders = 0 # 
        self.open_orders = None
        
        if btc:
            asks,bids = self.get_orderbook()
            self.tsize = convert_to_quote(asks, bids, tsize)
        else:
            self.tsize = tsize            
            
    
    def get_orderbook(self):       
        """
        This function only returns the orderbook if a minimum amount of 
        25 orders exists on both sides of the market. 
        Hence, if the condition is not satisfied, the market is automatically
        regarded as too illiquid to trade.
        """
        try:

            market = super().get_market(self.market_string)
            orderbook_df = pd.DataFrame(market.orderbook(self.orderbooklimit)) # 
            
            asks = orderbook_df['asks'] # prices increasing from index 0 to index 1
            bids = orderbook_df['bids'] # prices decreasing from index 0 to index 1
            
            return asks,bids 
        
        except Exception as e:
            
            print("Update failed, market is too illiquid: {}".format(e))
            return None, None            
    
    def run(self):
        
        i = 0
        
        while True:
            i += 1
            current_state = self.strategy.state
            print("Worker: {} .... running in state {} loop {}".format(self.market_string, current_state, i)) 
            asks, bids = self.get_orderbook()
            
            #state machine table
            if current_state == 0:
                price = self.strategy.state0(asks, bids)
                if price and self.amount_open_orders < self.max_open_orders:
                    order = super().buy(self.market_string, price, self.tsize)
                    w_order = {'order': order,'price': price, 'amount': self.tsize}
                    self.orders.append(w_order)  # on worker side
                    super().order_active(order, self.market_string)# register to manager
                    print("Worker: Order {} placed for {} @ {}".format(order['id'],w_order['amount'],w_order['price']))
                    
                    #switch to next state
                    self.strategy.state = 1
                    
            if current_state == 1:
                w_order = self.orders[-1]
                order = w_order['order']
                print("Worker: checking for order: {} ".format(order['id']))

                if super().order_active(order, self.market_string):
                
                    #order still open
                    # calculate spread
                    if self.strategy.state1(asks, w_order):
                        # all good
                        pass
                    else:
                        # spread not satisfied cancel order
                        # delete order from worker
                        print("Worker: deleting {}".format(self.orders.pop()))
                        # tell the manager to cancel the order
                        super().cancel(order, self.market_string)
                        self.strategy.state = 0 
                else:
                    # order not more active but we did not a
                    print("Worker: Filled order!")
                    

            time.sleep(1)