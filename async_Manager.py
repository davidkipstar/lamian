import json
import time 
import pandas as pd
import sys

from bitshares import BitShares
from bitshares.account import Account
from bitshares.market import Market

from utils import *

class Manager:
    """
    Manage:
     - buy, order, cancel of orders
     - balance
    """
    markets = {}
    
    def __init__(self):    
        self.instance = BitShares(witness_url = 'wss://eu-west-2.bts.crypto-bridge.org')    
        self.balances = {}
        self.orders = {}
        self.signup()
        self.balance()
        

    def signup(self):

        with open('credentials.json') as f:
            d = json.load(f)
            for key, value in d.items():
                setattr(self, key, value)
        self.account = Account(getattr(self, 'acc'),
                                bitshares_instance = self.instance)
        self.account.bitshares.wallet.unlock(getattr(self,'pw'))


    def buy(self, market_key, price, amount):
        #blockchain_instance
        market = self.get_market(market_key)
        print("Market unlocked {}".format(market.bitshares.wallet.unlocked()))
        print("Account unlocked {}".format(self.account.bitshares.wallet.unlocked()))
        order = market.buy(price = price, 
                            amount = amount, 
                            returnOrderId = True, 
                            account = self.account,
                            expiration = 60)
        
        d = {'orderid' : 123,
                    'price' : price,
                    'amount' : amount,
                    'order': order}
        return d      #self.orders[order['orderid']] = market

    def cancel(self, order):
        try:
            self.orders[order['orderid']].cancel(order['orderid'], self.account)
        except Exception as e:
            print("Error during cancellation! Order_id: {}".format(order['orderid']))

    def balance(self):
        self.account.refresh()
        my_coins = self.account.balances
        print("balance    : {}".format(my_coins))
        self.balances = dict(zip(map(lambda x: getattr(x,'symbol'),my_coins),my_coins))


    def get_market(self, market_key):
        #market_key = getattr(worker, 'quotecur') + ':' + getattr(worker, 'basecur')
        if market_key in Manager.markets.keys():
            print("Market: {} ".format(market_key))
            print(Manager.markets[market_key])    
            return Manager.markets[market_key]
        else:
            Manager.markets[market_key] = Market(market_key, blockchain_instance = self.instance)
            print("Market: {} ".format(market_key))
            print(Manager.markets[market_key])
            return Manager.markets[market_key]

    def pick_sellcoins(self, blacklist= ['BRIDGE.BTC','BTS', 'DEEX', 'FRESHCOIN', 'LIQPAY', 'READMEMO'],min_capital=0.00000001):
        #
        my_coins = []
        for coin in self.balances.values():
            if coin.symbol not in blacklist and coin.amount > min_capital:
                print("Added {} with balance {}".format(coin.symbol, coin.amount))
                my_coins.append(coin)
        return dict(zip(map(lambda x: getattr(x,'symbol'),my_coins),my_coins))

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
                print("Coinbalance for {} is {}".format(quotecur,quoteamount))
                #
                return quoteamount
            else:
                #Initial
                raise ValueError("Quotecur not found")

        except Exception as e:
            print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)


        