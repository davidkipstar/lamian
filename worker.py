import json
import time 
import pandas as pd

from bitshares import BitShares
from bitshares.account import Account
from bitshares.market import Market

from utils import *

from multiprocessing import Queue, Process
import multiprocessing
from manager import Manager

class Worker(Manager):

    def __init__(self, filename, q):
        super().__init__('credentials.json')
        self.settings(filename)
        self.state = None
        self.q = q
        self.signup()
        self.price_bid = None 
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


    def state0(self):
        #
        try:
            asks, bids = self.update()

            test_ask = find_price(asks, self.th_ask, self.init_tsize_ask)
            test_bid = find_price(bids, self.th_bid, self.init_tsize_bid)

            spread = (test_ask - test_bid)/test_bid
            spread = spread.quantize(satoshi)

            if spread > self.spread_th_bid:\
                self.q.put({'spread':spread})
                return True
        finally:
            return False 


    def state1(self, orderid, tsize_bid):
        # track of our own order
        asks, bids = self.update()

        #test_ask = find_price(asks, self.th_ask, self.init_tsize_ask)
        test_bid = find_price(bids, self.th_bid, tsize_bid, compensate_orders=True)

        #check for deviation between 
        bid_deviation = abs(update_prices_bid - price_bid)
        
        #
        open_orders = self.get_open_orders()
        if len(open_orders)==1:
            if bid_deviation > Decimal('0.0000000099'):
                self.q.put({'error':bid_deviation})
                raise ValueError("Price to high")
            else:
                return True
        elif len(open_orders) > 1:
            self.q.put({'error':"too many orders"})
            raise ValueError("Too many open orders, found {}".format(len(open_orders)))
        else:
            #dunno of filed expired or shit

            self.q.put({'error':"not enough orders"})
            raise ValueError("No open order found")


        except Exception as e:
            print("Error: {}".format(e))
        finally:
            return False


    def apply_strategy(self):
        try:
            #1 Checking spread
            if self.state == 0:
                while not self.state0():
                    #nothing to do
                    pass
                #the real deal
                asks,bids = self.update()
                tsize_bid = convert_to_quote(asks, bids)
                new_price = find_price(bids, self.th_bid, tsize_bid)
                #create order

                order_id = self.create_buy_order(tsize_bid, new_price)
                
                self.q.put({'order':order})
                if(order_id):
                    #success
                    self.state = 1 #change state 
                else:
                    print("Critical Error: order not places succesfully" )     
                    self.state = 0

            #2 Checking open_order
            if self.state ==1:
                while not self.state1():
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
            while self.state not None:
                if self.apply_strategy():
                    #done with one round

                    self.q.put({'Success':"Done"})
                    
        except Exception as e:
            print("Exception in run {}".format(e))
        
        finally:
            pass