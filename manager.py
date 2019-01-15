import json
import time 
import pandas as pd

from bitshares import BitShares
from bitshares.account import Account
from bitshares.market import Market

#from worker import Worker 

from multiprocessing import Queue, Process
import multiprocessing

class Manager:
    _currencies = {}
    
    def __init__(self, credentials):
        self.instance = BitShares()   
        self.q = Queue()
        self.workers = []
        self.orderids = []
        self.currencies = {}

        with open(credentials) as f:
            d = json.load(f)
            for key, value in d.items():
                setattr(self, key, value)

    def add_worker(self,filename):
        w = Worker(filename, self.q)
        if getattr(w,'basecur') in self.currencies.keys():
            self.currencies[getattr(w,'basecur')].append(w)
        else:
            self.currencies[getattr(w, 'basecur')] = [w]
        #self.workers.append(w)
        print("Added worker")
    
    def start(self):
        #this could be state 1: joining the market
        for currency, workers in self.currencies.items():
            for worker in workers:
                worker.state = None
                p = Process(target=Worker.run,args=(worker,))
                p.daemon = True
                p.start()
    
    def manage(self):
        #queue
        while True:
            x = self.q.get()
            #got signal from 
            #filter state 
            #apply strategy
            #continue or adjust
            print(x)
"""

"""


class Worker(Manager):

    def __init__(self, filename, q):
        super().__init__('credentials.json')
        self.settings(filename)
        self.state = None
        self.q = q
        self.signup()
        self.market = Market(self.quotecur + ':' + self.basecur)

    def signup(self):
        try:
            #load settings and unlock wallet
            self.instance.wallet.unlock(getattr(self,'pw'))
            if self.instance.wallet.unlocked():
                print("Unlocking wallet was successfull")
                self.acc = Account(getattr(self,'acc'), bitshares_instance=self.instance, full = True)
            else:
                raise ValueError("Unlocking not succesfull, check credentials.json")

            #join market

        except Exception as e:
            print("Error: {}".format(e))
    

    def settings(self, filename):
        # pose boundary on settings here if wanted
        with open(filename) as f:
            j = json.load(f)
            for key, value in j.items():
                setattr(self, key, value)
        
        #register to global Manager
        #if j['basecur'] in Manager._currencies.keys():
        #    super()._currencies[j['basecur']].append(self)
        #else:
        #    super()._currencies[j['basecur']] = [self]

    """
    From here on helpers function which do not process orderbook
    helpers function
    """

    #fetch orderbook
    def update(self):
        orderbook_df = pd.DataFrame(self.market.orderbook(self.orderbooklimit))

        asks = orderbook_df['asks'] # prices increasing from index 0 to index 1
        bids = orderbook_df['bids'] # prices decreasing from index 0 to index 1
        return asks,bids 

    #place buy order
    def create_buy_order(self, tsize_bid, optimal_bid):
        try:
            order = self.market.buy(price = optimal_bid, amount = tsize_bid, account = self.account, returnOrderId = True, expiration = 60) 
            #logging.info('Buy Order: {} for {} has id {}'.format(optimal_bid,tsize_bid,order))
            return order
    
        except Exception as e:
            #logging.warning('Failed buying!!')
            print("Failed buying: {}".format(e))
            return 0

    #place sell order 
    def create_sell_order(self, tsize_ask, optimal_ask):
       # make sure order is not place within asks
        try:
            order = self.market.sell(price = optimal_ask, amount = tsize_ask, account = self.account, returnOrderId = True, expiration = 60) 
            #logging.info('Sell Order: {} for {} has id {}'.format(optimal_ask,tsize_ask,order))
            return order
        except Exception as e:
            #logging.warning('Failed selling!!')
            print("Failed selling: {}".format(e))
            return 0    
            
    #cancel order by id
    def cancel_order(self, account, order): # pass return of create_order as input
        try:
            self.market.cancel(order['orderid'], self.account) # hier string ersetzen durch test order id
            return True
        except Exception as e:
            #logging.warning('Failed to cancel order')
            print("Failed canceling: {}".format(e))
            return False
            
    #retu
    def get_open_orders(self):
        try:
            self.account.refresh()
            open_orders = self.market.accountopenorders(account = self.account)
            return open_orders
        except Exception as e:
            print("Error getting open orders: {}".format(e))
            return None

    #
    def accountbalance(self):
        balance_l = self.account.balances
        basecur = self.basecur
        quotecur = self.quotecur
        baseidx = 0
        quoteidx = 0
        baseidx_found = False
        quoteidx_found = False
        for i in range(len(balance_l)):
            ele = balance_l[i]
            sym = ele['symbol']
            if(sym == basecur):
                baseidx = i
                baseamount = balance_l[baseidx]['amount']
                baseidx_found = True
            if(sym == quotecur):
                quoteidx = i
                quoteamount = balance_l[quoteidx]['amount']
                quoteidx_found = True
            if(baseidx_found == False):
                baseamount = None 
            if(quoteidx_found == False):
                quoteamount = 0
    
        return baseamount, quoteamount

    def apply_strategy(self):
        try:
            #1 Checking spread
            if self.state == 0:
                pass
                
            #2 Checking open_order
            if self.state ==1:
                pass
            
            raise ValueError("Fick dick")

        except Exception as e:
            print("Error in state {} with message {}".format(self.state, e))    
        finally:
            print("Strategy completed")
            return True
        #Finally Order filled

        print("Apply in state {}".format(self.state))
        self.state += 1
        if self.state == 10: return False
        else: return True
        #asign report 

    @staticmethod
    def run(self):
        """
        If state is None it is initialized
        """
        try:
            if self.state:
                print("Rejoining... not implemented")
                self.strategy = Strategy()
            else:
                for i in range(2):
                    self.state = i
                    if self.apply_strategy():
                        print("Switching to state {}".format(i))
                        self.state += 1
                        #create info for manager
                        self.q.put(getattr(self,'quotecur'))
            
        except Exception as e:
            print("Exception in run {}".format(e))
