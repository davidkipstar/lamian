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

class Proxy:
    pass


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


#            local_dir = os.listdir(os.getcwd())
#            for crypto_asset in balances:
#                crypto = crypto_asset.symbol+'.json'
#                if crypto in local_dir:
#                    # we have settings and cash
#                    for other_crypto in local_dir: #LCC.json    

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



class Worker:

    def __init__(self, filename, q, tsize, btc=True):
        self.settings(filename)
        witness_url = 'wss://eu-west-2.bts.crypto-bridge.org'
        self.instance = BitShares(instance=witness_url)      
        self.q = q
        self.price_bid = None 
        self.order_ids = []
        self.state = None
        
        #init_start
        self.signup()

        if self.establish_connection():
            print("Ready to go ")
        #
        if btc:
            # Buy
            asks,bids = self.update()
            self.tsize = convert_to_quote(asks, bids, tsize)
        else:
            # Sell
            self.tsize = tsize
        
        
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
        

    """
    From here on helpers function which do not process orderbook
    helpers function
    """

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


    def state0(self):
        #
        try:
            asks, bids = self.update()
            satoshi = Decimal('0.00000001')
            test_ask = find_price(asks, getattr(self, 'th_ask'), getattr(self, 'start_tsize_ask'))
            test_bid = find_price(bids, getattr(self, 'th_bid'), getattr(self, 'start_tsize_bid'))

            spread = (test_ask - test_bid)/test_bid
            spread = spread.quantize(satoshi)

            print("Spread@{}".format(spread))
            if spread > self.spread_th_bid:
                self.q.put({'spread':spread})
                return True
            else:
                self.q.put({'small_spread':spread})
        except Exception as e:
            print("Error in state0: {}".format(e))
        finally:
            return False 


    def state1(self, orderid):
        try:
            # track of our own order
            asks, bids = self.update()

            #test_ask = find_price(asks, self.th_ask, self.init_tsize_ask)
            test_bid = find_price(bids, self.th_bid, self.tsize_bid, compensate_orders=True)

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

    def establish_connection(self):
        for i in range(5):
            time.sleep(5)
            try:
                if i: print("Reconnecnting try nmbr {}".format(i))
                self.signup()
                self.market = Market(getattr(self,'quotecur') + ':' + getattr(self,'basecur'))
                self.market.bitshares.wallet.unlock(getattr(self,'pw'))
                if self.market.bitshares.wallet.unlocked(): break;
                else: raise ValueError("Connecting failed")
            except Exception as e:
                print("Error in connecting to node {}".format(e))
        return True


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