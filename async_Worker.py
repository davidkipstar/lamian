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

    def __init__(self, quote, base, tsize, tradingside = 'buy', th = 0.05, prev_order = None):
        super().__init__()
        #settings for trade 
        self.tradingside = tradingside
        self.th = th
        
        #
        self.orderbooklimit = 25
        self.max_open_orders = 1
        self.price_bid = None 
        self.open_order = prev_order
        self.state = None
        self.history = []
        self.cur = quote
        #setup
        if self.tradingside == 'buy':
            self.base, self.quote = base, quote
            self.market_string = "BRIDGE.{}:BRIDGE.{}".format(quote, base)
            super().get_market(self.market_string)
            asks, bids = self.get_orderbook(self.market_string)
            self.tsize = convert_to_quote(asks, bids, tsize)
            self.max_inventory = self.tsize # has to be denominated in quote
        
        else:
            self.base, self.quote = quote, base
            self.market_string = "BRIDGE.{}:BRIDGE.{}".format(quote, base)
            super().get_market(self.market_string)
            asks, bids = self.get_orderbook(self.market_string)
            self.tsize = tsize
            self.max_inventory = convert_to_base(asks, bids, tsize)

        print("Worker on {}".format(self.market_string))

        #Strategy
        self.strategy = CheckSpread(tsize=self.tsize,th=self.th, tradingside = self.tradingside)
        self.max_open_orders = 2
                         
    def run(self):
        i = 0
        while True:
            i += 1
            current_state = self.strategy.state
            #
            
            if i % 5 == 0:    
                print(" -------------------------------------------")
                print("Worker: {} .... running in state {} loop {}".format(self.market_string, current_state, i)) 
                print("Recent Trades By Worker: ")
                for order in self.open_orders:
                    print(" -------------------------------------------")
                    print("Open Orders: {}".format(order))
                print(" -------------------------------------------")

            time.sleep(2)
            asks, bids = self.get_orderbook(self.market_string)
            
            #state machine table
            if current_state == 0:
                open_orders = self.open_orders
                amount_open_orders = len(open_orders)
                price = self.strategy.state0(asks, bids)
                if price and amount_open_orders < self.max_open_orders: #and self.amount_open_orders < self.max_open_orders:
                    order = super().buy(self.market_string, price, self.tsize)
                    w_order = {'order': order,'price': price, 'amount': self.tsize}
                    Manager.orders.append(w_order)
                    self.open_order = w_order.copy()
                    print("Placed for {} at {}".format(price, self.tsize))
                    self.strategy.state = 1
                    
            if current_state == 1:

                w_order = self.open_order
                #print("Worker: checking for order: {} ".format(order['id']))
                if self.order_active(w_order, self.market_string):
                    if not self.strategy.state1(bids, w_order):
                        # spread not satisfied cancel order
                        print("Canceling order in Manager ....")
                        if super().cancel(w_order, self.market_string):
                            del self.open_order #write function to delete the correct order
                            self.strategy.state = 0 
                        else:
                            raise ValueError("Cancelling not successfull")
                else:
                    filled, recent_trades =  super().order_filled(w_order, self.market_string)
                    if filled:
                        print("Order was filled...")
                        avg_price = calc_avg_price(recent_trades, self.tradingside)

                        # Adjust tsize
                        cur_bal = super().balance()[self.cur]
                        self.tsize = max(self.max_inventory - cur_bal, 0)
                        print("New tsize {} , avg_price {}".format(self.tsize, avg_price))
                        #get new balance
                        #switch sideS? 
                    else:
                        print("Order expired...")
                        self.strategy.state = 0
                    