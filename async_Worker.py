import json
import time 
import pandas as pd
import sys
#import asnycio 
from bitshares import BitShares
from bitshares.account import Account
from bitshares.market import Market

from utils import *

from Strategy import CheckSpread
from async_Manager import Manager


class Worker(Manager):

    def __init__(self, buy, sell, tsize, th = 0.05, base='buy'):

        #


        #settings for trade 

        self.orderbooklimit = 25
        self.price_bid = None 
        self.orders = []
        self.state = None
        
        #setup
        self.market_string = "BRIDGE.{}:BRIDGE.{}".format(buy, sell)
        print("Worker on {}".format(self.market_string)) 
        
        if base == 'buy':
            base = buy
            quote = sell
            super().__init__([base, quote]) 
            asks,bids = self.get_orderbook(self.market_string)
            self.tsize = tsize

        else:
            base = sell
            quote = buy
            super().__init__([base, quote]) 
            asks,bids = self.get_orderbook(self.market_string)
            self.tsize = convert_to_quote(asks, bids, tsize)
        
        #base,quote

        self.strategy = CheckSpread(tsize=self.tsize,th=th)
        
        self.max_open_orders = 1
        
        # Below: Depends on Manager input
        self.keep_buying = None
        self.do_cancel = None
        self.amount_open_orders = 0 # 
        
        #
                 
    def run(self):
        #
        i = 0
        while True:
            i += 1
            current_state = self.strategy.state
            print("Worker: {} .... running in state {} loop {}".format(self.market_string, current_state, i)) 
            asks, bids = self.get_orderbook(self.market_string)
            
            #state machine table
            if current_state == 0:
                price = self.strategy.state0(asks, bids)
                if price and self.amount_open_orders < self.max_open_orders:
                    order = super().buy(self.market_string, price, self.tsize)
                    w_order = {'order': order,'price': price, 'amount': self.tsize}
                    Manager.orders.append(w_order)
                    self.orders.append(w_order)  # on worker side
                    self.order_active(w_order, self.market_string)
                    print("Bought")
                    self.strategy.state = 1
                    
            if current_state == 1:
                w_order = self.orders[-1]
                print("Worker: checking for order: {} ".format(order['id']))

                if self.order_active(w_order, self.market_string):
                
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