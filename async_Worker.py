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
        self.max_open_orders = 1
        # Below: Depends on Manager input
        self.keep_buying = None
        self.do_cancel = None
        self.amount_open_orders = 0 # assumption
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
                if price and self.amount_open_orders < self.max_open_orders:
                    test_order = super().buy(self.market_string, price, self.tsize)
                    self.orders.append(test_order)  # on worker side
                    print('tracked orders:', self.orders)

                    a = self.get_all_open_orders()
                    b = self.get_asset_open_orders(self.market_string)
                    c = self.cancel_all_orders(self.market_string)
                    print('a,b,c:')
                    print(a, b, c)

                    print('sending to manager:')
                    self.order_active(b)

                    # Find which orders in Manager.orders are still active
                    print('these orderidss are still active ', self.which_orderids_still_active())

                    # Instantly cancel order, for testing!
                    if test_order and not c:
                        print('order is set, trying to cancel')
                        test_cancel = self.cancel(test_order, self.market_string)
                        if test_cancel:
                            print('cancellation successful')
                        else:
                            print('couldnt cancel order, abort mission!!! Require manual cancellation!')



# BREAK
                    current_state = 1

            if current_state == 1:
                order = self.orders[-1]
                # self.keep_buying muss vom Manager runterkommuniziert werden!
                if self.keep_buying:  #super().order_active(order):
                    self.strategy.state1(asks, self.orders[-1])
                else:
                    self.strategy.state = 0

            time.sleep(1)

            """                 

                                # Test recent functions
                                a = self.get_all_open_orders()
                                b = self.get_asset_open_orders(self.market_string)
                                c = self.cancel_all_orders(self.market_string)
                                print(a, b, c)

                                # Instantly cancel order, for testing!
                                if test_order and not c:
                                    print('order is set, trying to cancel')
                                    test_cancel = self.cancel(test_order, self.market_string)
                                    if test_cancel:
                                        print('cancellation successful')
                                    else:
                                        print('couldnt cancel order, abort mission!!! Require manual cancellation!')

            """

            """

                                self.open_orders = self.get_asset_open_orders(self.market_string)
                                print('Worker: Found open orders: ', self.open_orders)
                                self.amount_open_orders = len(self.open_orders)
                                self.order_active(self.open_orders)  # send to manager

                                self.cancel_all_orders(self.market_string)

            """