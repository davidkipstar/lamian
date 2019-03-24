import json
import time 
import pandas as pd
import numpy as np
import sys

from bitshares import BitShares
from bitshares.account import Account
from bitshares.market import Market

from utils import *

"""
The Manager:

"""

class Manager:
    
    markets = {}
    url = 'wss://eu-west-2.bts.crypto-bridge.org'
    orders = []
    instance = None


    def __init__(self):#, currencies):
        print("---- init Manager -----")
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
        
        #Add markets
        #for shitcoin in currencies[1:]:
        #    m = self.get_market("BRIDGE.{}:BRIDGE.{}".format(currencies[0],shitcoin))
        
    def balance(self):
        self.account.refresh()
        my_coins = self.account.balances
        return dict(zip(map(lambda x: getattr(x,'symbol'),my_coins),my_coins))

    def check_balance(self, quote, base, market_string, tradingside):
        market = self.get_market(market_string)

        _balances = self.balance()
        recent_trades = []
        for trade in market.accounttrades(account=self.account): #[0]
            if trade not in self.history:
                print("New Trade found {}".format(trade))
                recent_trades.append(trade)
        
        self.history.extend(recent_trades)
        
        avg_price = calc_avg_price(recent_trades, tradingside)

        if tradingside == 'buy':
            if quote in _balances.keys():
                coinbalance = _balances[quote]
            else:
                coinbalance = 0    
        else:
            if base in _balances.keys():
                coinbalance = _balances[base]
        tsize = min(coinbalance - 0.00000001, 0)
        
        return tsize, avg_price

    @property
    def open_orders(self):
        self.account.refresh()
        open_orders = self.account.openorders
        return open_orders

    def which_orderids_still_active(self):
        #
        all_open_orders = self.open_orders
        all_open_orderids = []
        manager_orderids = []

        # Get all currently active orderids
        for i in range(len(all_open_orders)):
            all_open_orderids.append(all_open_orders[i]['id'])

        # Get all orderids from Manager.orders
        for i in range(len(Manager.orders)):
            manager_orderids.append(Manager.orders[i]['order']['orderid'])

        # Compare, find out which tracked orders on the manager side are still open
        still_open_orders = [item for item in manager_orderids if item in all_open_orderids]

        return still_open_orders

    def order_active(self, order, market_string):
        print("Manager-orders")

        order_found = False
        open_orders = self.open_orders
        for morder in open_orders:
            print("Comparing {} with {}".format(morder['id'], order['order']['orderid']))
            if morder['id'] == order['order']['orderid']: 
                order_found = True
        
        return order_found

    def buy(self, market_key, price, amount):
        market = self.get_market(market_key)
        order = market.buy(price = price,
                            amount = amount,
                            returnOrderId = True,
                            account = self.account,
                            expiration = 10)
        self.account.refresh()
        return order

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
        if market_key in Manager.markets.keys():
            return Manager.markets[market_key]
        else:
            market = Market(market_key, blockchain_instance = Manager.instance)
            market.bitshares.wallet.unlock(self.pw)
            Manager.markets[market_key] = market
            print("Joined market {}".format(market_key))
            return Manager.markets[market_key]

