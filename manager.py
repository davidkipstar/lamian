import json
import time 
import pandas as pd

from bitshares import BitShares
from bitshares.account import Account
from bitshares.market import Market

#from worker import Worker 
from utils import *

from multiprocessing import Queue, Process
import multiprocessing

from worker import Worker




class Manager:

    _currencies = {}
    _balances = {}
    _instance = None
    
    def __init__(self, credentials):
        #Connecting to API server: 'wss://eu-west-3.bts.crypto-bridge.org/'
        #Proxy
        witness_url = 'wss://eu-west-2.bts.crypto-bridge.org'
        self.instance = BitShares(instance=witness_url)    
        self.balances = {}
        self.q = Queue()
        self.workers = []
        self.orderids = []
        self.currencies = {}

    #Insert to proxy
    def signup(self):
        try:
            with open('credentials.json') as f:
                d = json.load(f)
                for key, value in d.items():
                    setattr(self, key, value)

            self.account = Account(self.acc)
            self.account.refresh()
        except Exception as e:
            print("E: {}".format(e))
        finally:
            return self

    def add_worker(self,filename, tsize,btc=True):
        #
        w = Worker(filename, self.q, tsize,btc=btc)
        if getattr(w,'basecur') in self.currencies.keys():
            self.currencies[getattr(w,'basecur')].append(w)
        else:
            self.currencies[getattr(w, 'basecur')] = [w]
        #self.workers.append(w)
        print("Added worker")
    
    
    def settings(self, filename):
        # pose boundary on settings here if wanted
        print('Filename : {}'.format(filename))
        base, quote = filename.split(':')
        with open('standard-settings.json') as f:
            j = json.load(f)
            for key, value in j.items():
                setattr(self, key, value)
        setattr(self, 'basecur', base)
        setattr(self, 'quotecur', quote)

    def start(self):
        #this could be state 1: joining the market
        for currency, workers in self.currencies.items():
            for worker in workers:
                worker.state = None
                p = Process(target=Worker.run,args=(worker,))
                p.daemon = True
                p.start()

    def initial_balance(self):
        #
        try:
            #
            self.account.refresh()
            my_coins = self.account.balances
            print("balance    : {}".format(my_coins))

            self.balances = dict(zip(map(lambda x: getattr(x,'symbol'),my_coins),my_coins))

            #
        except Exception as e:
            print("Error {}".format(e))


    def pick_sellcoins(self, blacklist= ['BRIDGE.BTC','BRIDGE.BTS'],min_capital=0.00000001):
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
            print("E in coinbalance : {}".format(e))

    def listen(self):
        #
        return True

