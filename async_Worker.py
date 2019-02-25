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
            self.tsize = tsize
        
        else:
            asks,bids = self.get_orderbook()
            self.tsize = convert_to_quote(asks, bids, tsize)
            
            
                        
        """
        get_orderbook:
        This function only returns the orderbook if a minimum amount of 
        25 orders exists on both sides of the market. 
        Hence, if the condition is not satisfied, the market is automatically
        regarded as too illiquid to trade.
        """
                    
    def get_orderbook(self):
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
            print(asks)
            print(bids)
            for order in self.orders:
                print("Open order {}".format(order))
            #state machine table
            if current_state == 0:
                price = self.strategy.state0(asks, bids)
                if price:
                    order = super().buy(self.market_string, price, self.tsize)
                    self.orders.append(order)
            if current_state == 1:
                order = self.orders[-1]
                if order['orderid'] ==0:
                    print("Error placing order")
                else:
                    print("Worker: {} order {} placed,  amount: {}  price: {}".format(self.market_string, 
                                                                                        order['orderid'],
                                                                                        order['amount'],
                                                                                        order['price']))
                    self.strategy.state1(asks, self.orders[-1])

            time.sleep(3)