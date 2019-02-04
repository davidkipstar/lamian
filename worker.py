import json
import time 
import pandas as pd

from bitshares import BitShares
from bitshares.account import Account
from bitshares.market import Market
from bitshares.asset import Asset

#from worker import Worker 
from utils import *

from multiprocessing import Queue, Process
import multiprocessing


class Proxy:
    _instance = None
    _queue = None
    _pwd = None
    def __init__(self):
        if Proxy._instance is None:
            with open('credentials.json') as f:
                d = json.load(f)
                for key, value in d.items():
                    setattr(self, key, value)
            self.account = Account(self.acc)
            self.account.refresh()
            Proxy._pwd = self.pw
            witness_url = 'wss://eu-west-2.bts.crypto-bridge.org'
            Proxy._instance = BitShares(instance=witness_url)      
        if Proxy._queue is None:
            Proxy._queue = Queue()   
    

    def put(self,event):
        #process event here
        Proxy._queue.put(event)

    @staticmethod
    def getQueue():
        #get event
        return Proxy._queue.get()
    @staticmethod
    def getPwd():
        return Proxy._pwd
    @staticmethod
    def getInstance():
        return Proxy._instance

class Worker(Proxy):

    def __init__(self, qcoin, bcoin, **kwargs):
        """


        kwargs are or ordered dict?
        strategy:
          -- state 0: Wait for Conditioin (large spread)
          -- state 1: Take Action (place order)
          -- state 2: Track Action (readjust order or quit)
        """
        super().__init__()
        #time.sleep(3)
        self.market = Market(
                qcoin,
                bcoin,
                bitshares_instance = Proxy._instance)
        
        self.market.bitshares.wallet.unlock(self.getPwd())
        self.strategy = kwargs 
   
    #fetch orderbook
    def update(self):
        try:
            orderbook_df = pd.DataFrame(self.market.orderbook(self.orderbooklimit))

            asks = orderbook_df['asks'] # prices increasing from index 0 to index 1
            bids = orderbook_df['bids'] # prices decreasing from index 0 to index 1
            return asks,bids 
        except Exception as e:
            print("Error : {}".format(e))
            return None, None
    
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






    def apply_strategy(self):
        try:

            if not self.establish_connection():
                raise ValueError("No connection established")

            #1 Checking spread
            if self.state == 0:
                while not self.state0():
                    #nothing to do
                    #print("HALLO")
                    time.sleep(10)
                    pass
                #the real deal
                asks,bids = self.update()
                tsize_bid = convert_to_quote(asks, bids, self.tsize)
                new_price = find_price(bids, getattr(self, 'th_bid'), tsize_bid)
                #create order
                order_id = self.create_buy_order(tsize_bid, new_price)
                self.order_ids.append(order_id)
                d = {'order':order_id,
                      'price': new_price,
                      'tsize': tsize_bid}
                
                self.q.put({getattr(self, 'quotecur') : d})

                if(order_id):
                    #success
                    self.state = 1 #change state 
                else:
                    print("Critical Error: order not places succesfully" )     
                    self.state = 0

            #2 Checking open_order
            if self.state ==1:
                while not self.state1(order_id, tsize_bid):
                    time.sleep(10)
                    #nthng to do 
                    pass
                #check if filed 
                self.state = 0

        except Exception as e:
            print("Error in state {} with message {}".format(self.state, e))    
        finally:
            print("Strategy completed")
            return True
        #Finally Order filled

    @staticmethod
    def run(self):
        """
        If state is None it is initialized
        """
        try:
            if not self.state:
                self.state = 0  
            while self.state is not None:
                #when state is 1 orderid and tsize of order need to be added to object
                if self.apply_strategy():
                    #done with one round

                    self.q.put({'Success':"Done"})
                    
        except Exception as e:
            print("Exception in run {}".format(e))
        
        finally:
            pass


if __name__ == '__main__':
    #
    base = Asset('BRIDGE.BTC')
    quote = Asset('BRIDGE.LCC')
    w = Worker(quote, base)
    Worker.run(w, strategy)
    #
