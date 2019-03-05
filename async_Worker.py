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
        super().__init__()
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
                
        market = super().get_market(self.market_string)
        try:
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
            print("Worker: {} .... running in state {} loop {}".format(self.market_string, self.strategy.state, i)) 
            current_state = self.strategy.state
            asks, bids = self.get_orderbook()  
            for order in self.orders:
                print("Open order {}".format(order))
            #state machine table
            if current_state == 0:
                price = self.strategy.state0(asks, bids)
                if price:
                    test_order = super().buy(self.market_string, price, self.tsize)
                    if test_order:
                        print('order is set, trying to cancel')
                        test_cancel = self.cancel(test_order, self.market_string)
                        if test_cancel:
                            print('cancellation succesful')
                        else:
                            print('couldnt cancel order, abort mission!!! Require manual cancellation!')

                    self.orders.append(order)
            if current_state == 1:
                order = self.orders[-1]
                if super().order_active(order):
                    self.strategy.state1(asks, self.orders[-1])
                else:
                    self.strategy.state = 0
            time.sleep(3)