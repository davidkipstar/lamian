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
    orders = []
    instance = None

    def __init__(self, acc):
        self.account = acc
        url = 'wss://eu-west-2.bts.crypto-bridge.org'
        if Manager.instance is None:
            Manager.instance = BitShares(witness_url = url)
        self.pw = "5KgkgfK4suQqLJY1Uv8mY4tPx4e8V8a2q2SX8xbS5o8UN9rxBJJ"
        self.balance()
        self.all_open_orders = self.get_all_open_orders()

    @classmethod
    def from_credentials(cls, filename, url = ''):
        #filename
        with open('credentials.json') as f:
            d = json.load(f)
        
        url = 'wss://eu-west-2.bts.crypto-bridge.org'
        instance = BitShares(witness_url = url)
        account = Account(d['acc'], bitshares_instance = instance)
        account.bitshares.wallet.unlock(d['pw'])
        print("Manager: Account unlocked: {}".format(account.bitshares.wallet.unlocked()))
        return cls(acc = account)
    
    def get_asset_open_orders(self, market_key):
        # Retrieves open orders for SPECIFIC market
    
        market = self.get_market(market_key)
        open_orders = market.accountopenorders(account=self.account)
        return open_orders
        """
        except Exception as e:
            print('Could not retrieve open orders!')
            return False
        """
    
    def get_all_open_orders(self):
        # Retrieves open orders for ALL assets
        #try:
        self.account.refresh()
        open_orders = self.account.openorders
        return open_orders
        """
        except Exception as e:
            print('Could not retrieve open orders!')
            return False
        """

    def order_active(self, order, market_string):
        print(Manager.orders)
        if order in Manager.orders:
            all_open_orders = self.get_asset_open_orders(market_string)

            #k = list(map(lambda x: getattr(x, 'id'),all_open_orders))
            #print("OpenOrder:",k)
            print("ORderId:", all_open_orders)
            if True:
                #
                print("Manager: Order still open")
                return True    
            else:
                #
                return False

        else:
            #new order signed up
            print("New order: {}".format(order))
            Manager.orders.append(order)
            return True


    def buy(self, market_key, price, amount):

        #blockchain_instance
        market = self.get_market(market_key)
        #print("ManaMarket unlocked {}".format(market.bitshares.wallet.unlocked()))
        #print("Account unlocked {}".format(self.account.bitshares.wallet.unlocked()))
        print("Manager: Placing order on {} for {} @ {}".format(market_key, price, amount))
        
        order = market.buy(price = price,
                            amount = amount,
                            returnOrderId = True,
                            account = self.account,
                            expiration = 60)


        return order

    def cancel(self, order, market_key):
        # cancelling specific order
        try:
            market = self.get_market(market_key)

            market.cancel(order['id'], self.account)
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
            orders = self.get_asset_open_orders(market_key)
            print((len(orders), 'open orders to cancel'))
            if len(orders):
                attempt = 1
                order_list = []
                for order in orders:
                    order_list.append(order['id'])

            while attempt:
                try:
                    details = market.cancel(order_list, self.account)
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

    def balance(self):
        self.account.refresh()
        my_coins = self.account.balances
        #print("balance    : {}".format(my_coins))
        self.balances = dict(zip(map(lambda x: getattr(x,'symbol'),my_coins),my_coins))


    def get_market(self, market_key):
        #market_key = getattr(worker, 'quotecur') + ':' + getattr(worker, 'basecur')
        if market_key in Manager.markets.keys():
            #print("Market: {} ".format(market_key))
            #print(Manager.markets[market_key])    
            return Manager.markets[market_key]
        else:
            market = Market(market_key, blockchain_instance = Manager.instance)
            market.bitshares.wallet.unlock(self.pw)
            Manager.markets[market_key] = market
            #print("Market: {} ".format(market_key))
            #print(Manager.markets[market_key])
            return Manager.markets[market_key]

    def pick_sellcoins(self, whitelist=['BRIDGE.LCC'], min_capital=0.00000001):
        #
        my_coins = []
        for coin in self.balances.values():
            if coin.symbol in whitelist and coin.amount > min_capital:
                print("Manager: Added {} with balance {}".format(coin.symbol, coin.amount))
                my_coins.append(coin)
        return dict(zip(map(lambda x: getattr(x, 'symbol'), my_coins), my_coins))

    def coinbalance(self, quotecur):
        """
          Withdrawls balance for one currency 
          If quotecur is None check all 
        """
        try:
            #maybe check for quote in some place
            if quotecur:
                balance_l = self.account.balances
                quoteidx = 0
                quoteidx_found = False
                for i in range(len(balance_l)):
                    ele = balance_l[i]
                    sym = ele['symbol']

                    if(sym == quotecur):
                        quoteidx = i
                        quoteamount = balance_l[quoteidx]['amount']
                        quoteidx_found = True
                    
                    if(quoteidx_found == False):
                        quoteamount = 0
                #print("Coinbalance for {} is {}".format(quotecur,quoteamount))
                return quoteamount
            else:
                #Initial
                raise ValueError("Quotecur not found")

        except Exception as e:
            print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
