import json
import time 
import pandas as pd
import sys

import asyncio 

from arbitrage import ArbitrageException
#import asnycio 
from bitshares import BitShares
from bitshares.account import Account
from bitshares.market import Market

from utils import *

from Strategy import CheckSpread
from async_Manager import Manager


class Worker:

    def __init__(self, quote, base, account, q, instance, **kwargs):   
        
        self.pw = "5KgkgfK4suQqLJY1Uv8mY4tPx4e8V8a2q2SX8xbS5o8UN9rxBJJ"
        self.acc = "kipstar1337"
        self.instance = instance 
        self.q = q
        for key, arg in kwargs.items():
            setattr(self, key, arg)
        market_key = "{}:{}".format(quote, base)
        self.name = market_key
        setattr(self, 'market',  Market(market_key, block_instance = self.instance))#, blockchain_instance = self.instance)
        setattr(self, 'cur', quote)
        self.strategy = CheckSpread(tsize=self.tsize, 
                                    th  = self.th, 
                                    tradingside = self.tradingside)
            
        self.market.bitshares.wallet.unlock(self.pw)
        orderbook_df = pd.DataFrame(self.market.orderbook(self.orderbooklimit)) # 
        asks = orderbook_df['asks'] # prices increasing from index 0 to index 1
        bids = orderbook_df['bids'] # prices decreasing from index 0 to index 1
    
        #setup
        if self.tradingside == 'buy':
            self.base, self.quote = base, quote        
            self.tsize = convert_to_quote(asks, bids, self.tsize)
            self.max_inventory = self.tsize # has to be denominated in quote
        
        else:
            self.base, self.quote = quote, base
            self.max_inventory = convert_to_base(asks, bids, self.tsize)

    @classmethod
    def from_manager(cls, manager, instance,**kwargs):
        #switch here the markets if neceessary
        return cls(manager.buy, manager.sell, manager.account, manager.q, instance, **kwargs) 


    async def run(self, q):

        while True:
            print("Worker {}".format(self.name))
            await asyncio.sleep(3)
            orderbook_df = pd.DataFrame(self.market.orderbook(self.orderbooklimit)) # 
            asks = orderbook_df['asks'] # prices increasing from index 0 to index 1
            bids = orderbook_df['bids'] # prices decreasing from index 0 to index 1
            #self.asks, self.bids = asks, bids
            #q = getattr(self, 'q')#.format(self.manager_string))
            q.put_nowait(asks)
        """

        try:

            i = 0
            while True:
                i += 1
                current_state = self.strategy.state
                print(" -------------------------------------------")
                print("Worker: {} .... running in state {} loop {}".format(self.market_string, current_state, i)) 
                print("Recent Trades By Worker: ")
                for order in self.open_orders:
                    print(" -------------------------------------------")
                    print("Open Orders: {}".format(order))
                print(" -------------------------------------------")
                await asyncio.sleep(2) 

                
                asks, bids = self.get_orderbook(self.market_string)
                self.asks, self.bids = asks, bids
                #state machine table
                if current_state == 0:
                    open_orders = self.open_orders

                    amount_open_orders = len(open_orders)
                    print(amount_open_orders)
                    balance = super().coin_balance(self.cur)
                    price = self.strategy.state0(asks, bids)

                    if price and amount_open_orders < self.max_open_orders and balance > self.tsize: #and self.amount_open_orders < self.max_open_orders:
                        print("{} : condition met.. placing order".format(self.market_string))
                        self.price = price
                        self.amount = self.tsize
                        order = super().buy()#self.market_string, price, self.tsize)
                        w_order = {'order': order,'price': price, 'amount': self.tsize}
                        Manager.orders.append(w_order)
                        self.open_order = w_order.copy()
                        print("{} order placed for {} at {}".format(self.market_string, price, self.tsize))
                        self.strategy.state = 1
                    else:
                        if i % 5 == 0: print("{}: waiting for action".format(self.market_string))
                        
                elif current_state == 1:
                    w_order = self.open_order
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
                            self.strategy = CheckSpread(self.tradingside, tsize =self.tsize, th = self.th)
                            
                        else:
                            print("Order expired...")
                            self.strategy.state = 0
        except ArbitrageException as e:
            print("Arbitrage exception {}".format(e))
            self.arbitrage = True
        finally:
            print("Arbitrage is {}".format(self.arbitrage))
        """