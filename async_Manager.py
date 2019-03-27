import json
import time 
import pandas as pd
import numpy as np
import sys
import asyncio
from bitshares import BitShares
from bitshares.account import Account
from bitshares.market import Market

from utils import *


class Manager:
    
    markets = {}
    url = 'wss://eu-west-2.bts.crypto-bridge.org'
    orders = []
    instance = None
    

    def __init__(self):#, currencies):
        print("---- init Manager -----")
        self.arbitrage = 0
        #Sign Up
        if Manager.instance is None:
            Manager.instance = BitShares(witness_url = Manager.url)
        self.history = []
        self.pw = "5KgkgfK4suQqLJY1Uv8mY4tPx4e8V8a2q2SX8xbS5o8UN9rxBJJ"
        self.acc = "kipstar1337"
        account = Account(self.acc, bitshares_instance = Manager.instance, full = True)
        account.bitshares.wallet.unlock(self.pw)
        self.account = account
        print("Manager: Account unlocked: {}".format(account.bitshares.wallet.unlocked()))
        self.open_order = None 
        #self.workers = []
        self.workers = []
    
    @property
    def workers(self):
        return self.workers 
    
    @workers.setter
    def workers(self, worker):
        if worker not in self.workers:
            self.workers.append(worker)
        else:
            if worker.arbitrage:
                self.arbitrage = self.arbitrage + 1
    
    @workers.getter(self):
        return self.workers
    

    def balance(self):
        self.account.refresh()
        my_coins = self.account.balances
        return dict(zip(map(lambda x: getattr(x,'symbol'),my_coins),my_coins))
    
    def new_trade(self, market_string):
        market = self.get_market(market_string)
        recent_trades = []
        for trade in market.accounttrades(account=self.account):
            if trade not in self.history:
                print("New Trade found {}".format(trade))
                recent_trades.append(trade)
            else:
                print("Recent trade: {}".format(trade))
        if recent_trades:
            self.history.extend(recent_trades)
        return recent_trades

    def order_filled(self, w_order, market_string):
        order_was_filled = False
        recent_trades = self.new_trade(market_string)
        if recent_trades:
            order_was_filled = True
        return order_was_filled, recent_trades

    @property
    def open_orders(self):
        if self.open_order is not None:
                
            self.account.refresh()
            #mkt = self.get_market(self.market_string)
            open_orders = self.account.openorders
            #market_open_orders = mkt.accountopenorders(account = self.account)
            return open_orders
        else:
            return []

    async def run(self):
        #
        while True:
            
            just_do_it = False
            if self.arbitrage > 1:
                workers = self.workers
                buy_worker, sell_worker = None, None
                for worker in workers:
                    #print("Manager: {}".format(worker.market_string))    
                    if worker.arbitrage:
                        #
                        for second_worker in workers:
                            if second_worker.arbitrage and worker != second_worker:
                                # unique worker on market
                                print("Arbtirage true in {} and {}".format(worker,second_worker))
                                if second_worker.cur == worker.cur:
                                    #
                                    if worker.tradingside == 'buy' and second_worker.tradingside == 'sell':
                                        if worker.price > second_worker.price:
                                            just_do_it = True
                                            buy_worker, sell_worker = worker, second_worker
                                            break;
                                    elif worker.tradingside == 'sell' and second_worker.tradingside == 'buy':
                                        if worker.price < second_worker.price:
                                            just_do_it = True
                                            buy_worker, sell_worker = second_worker, worker
                                            break;
            if just_do_it and buy_worker and sell_worker:
                
                print("Arbitrage")
                df = buy_worker.bids['price'] > sell_worker.asks['price']
                
                buy_side = buy_worker.bids[df]['price'].cumsum()
                sell_side = sell_worker.asks[df]['price'].cumsum()

                to_buy_amount, to_sell_amount = 0,0
                balance = self.balance()
                if buy_side.cur in balance:
                    to_buy_amount = balance[buy_side.cur] 
                if sell_side.cur in balance:
                    to_sell_amount = balance[sell_side.cur]            
                
                # check if max for seller is true
                buyer_price = max(buy_worker.bids[df]['price'])
                seller_price = max(sell_worker.asks[df]['price'])

                buy_worker.amount = to_buy_amount
                sell_worker.amount = to_sell_amount
                Manager.buy(buy_worker, price = buyer_price, amount = to_buy_amount)
                Manager.buy(sell_worker, price = seller_price, amount = to_sell_amount)
                self.arbitrage = 0 
                just_do_it = False
            await asyncio.sleep(10)



    def which_orderids_still_active(self):
        all_open_orders = self.open_orders
        all_open_orderids = []
        manager_orderids = []

        for i in range(len(all_open_orders)):
            all_open_orderids.append(all_open_orders[i]['id'])

        # Get all orderids from Manager.orders
        for i in range(len(Manager.orders)):
            manager_orderids.append(Manager.orders[i]['order']['orderid'])

        # Compare, find out which tracked orders on the manager side are still open
        still_open_orders = [item for item in manager_orderids if item in all_open_orderids]

        return still_open_orders

    def order_active(self, order, market_string):
        #print("Manager-orders")
        order_found = False
        open_orders = self.open_orders
        for morder in open_orders:
            #print("Comparing {} with {}".format(morder['id'], order['order']['orderid']))
            if morder['id'] == order['order']['orderid']: 
                order_found = True
        print("Order found: {}".format(order_found))
        return order_found
    
    @staticmethod
    def buy(self):#, market_key, price, amount):
        amount = self.amount 
        price = self.price 
        market = self.get_market(self.market_key)

        order = market.buy(price = price,
                            amount = amount,
                            returnOrderId = True,
                            account = self.account,
                            expiration = 60)
        self.account.refresh()
        return order

    def coin_balance(self, coin):
        #
        balance = self.balance()
        if coin in balance:
            return balance[coin]
        else:
            return 0

    def cancel(self, order, market_key):
        # cancelling specific order
        try:
            market = self.get_market(market_key)
            market.cancel(order['order']['orderid'], account = self.account)
            return True
        except Exception as e:
            print("Error during cancellation! Order_id: {}".format(order['id']))
            print(e)
            return False

    def cancel_all_orders(self, market_key, order_list = None):
        """
        So far this function cancels all orders for a specific market.
        However, it is desirable to manually pass a list of orderids that are supposed to be cancelled.
        This is currently under construction as we also need to manually pass the markets OR retrieve them
        via their asset id from the order
        """
        if not order_list:

            # Create list of orders to be cancelled, depending on a specific market
            # TODO we are actually signing up twice in the same market because get_market_open_orders requires a market too
            market = self.get_market(market_key)
            orders = self.open_orders
            print((len(orders), 'open orders to cancel'))
            if len(orders):
                attempt = 1
                order_list = []
                for order in orders:
                    order_list.append(order['id'])

            while attempt:
                try:
                    details = market.cancel(order_list, account  = self.account)
                    print(details)
                    attempt = 0
                    return True
                except:
                    print((attempt, 'cancel failed', order_list))
                    attempt += 1
                    if attempt > 3:
                        print('cancel aborted')
                        return False
                    pass

    def get_orderbook(self,market_string):
        try:
            market = self.get_market(market_string)
            orderbook_df = pd.DataFrame(market.orderbook(self.orderbooklimit)) # 
            
            asks = orderbook_df['asks'] # prices increasing from index 0 to index 1
            bids = orderbook_df['bids'] # prices decreasing from index 0 to index 1
            
            return asks,bids 
        
        except Exception as e:
            
            print("Update failed, market is too illiquid: {}".format(e))
            return None, None       

    def get_market(self, market_key):
        if self not in Manager.workers:
            Manager.workers.append(self)
        if market_key in Manager.markets.keys():
            return Manager.markets[market_key]
        else:
            market = Market(market_key, blockchain_instance = Manager.instance)
            market.bitshares.wallet.unlock(self.pw)
            Manager.markets[market_key] = market
            print("Joined market {}".format(market_key))
            return Manager.markets[market_key]

