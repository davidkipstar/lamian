from utils import find_price, convert_to_quote
from decimal import Decimal

import pandas as pd

from bitshares import BitShares
from bitshares.account import Account
from bitshares.market import Market
from arbitrage import ArbitrageException

class CheckSpread:
    satoshi = Decimal('0.00000001')        
    """
        market: market
        tsize : tsize
        tradingside: 
        toQuote:
        account: account

    """
    def __init__(self, **kwargs):
        for key, arg in kwargs.items():
            setattr(self, key, arg)
        if kwargs['toQuote']:        
            asks, bids = self.orderbook
            if asks is None:
                self.orderbooklimit = self.orderbooklimit//2
                asks, bids = self.orderbook
                if asks is None:
                    print("FAILED MISSERABLY")
            if asks is not None:
                self.tsize = convert_to_quote(asks, bids, self.tsize)

    @classmethod
    def from_kwargs(cls, **kwargs):
        instance = BitShares(witness_url = kwargs['url'])
        account = Account(kwargs['acc'], bitshares_instance = instance, full = True)
        account.bitshares.wallet.unlock(kwargs['pw'])
        kwargs.update({'account' : account, 'instance': instance})
        return cls(**kwargs)

    @property 
    def orderbook(self):
        ob = self.market.orderbook(self.orderbooklimit)
        if len(ob['asks']) >= self.orderbooklimit and len(ob['asks']) >= self.orderbooklimit:
            asks, bids = pd.DataFrame(ob['asks']), pd.DataFrame(ob['bids'])
            return asks, bids 
        else:
            print("not liquid")
            return None, None

    
    @property
    async def open_orders(self):
        self.account.refresh()
        open_orders = self.account.openorders
        return open_orders
    
   
    def order_filled(self, w_order, market_string):
        order_was_filled = False
        recent_trades = self.new_trade(market_string)
        if recent_trades:
            order_was_filled = True
        return order_was_filled, recent_trades


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

    def order_active(self, order):
        #print("Manager-orders")
        order_found = False
        open_orders = self.open_orders
        for morder in open_orders:
            #print("Comparing {} with {}".format(morder['id'], order['order']['orderid']))
            if morder['id'] == order['order']['orderid']: 
                order_found = True
        print("Order found: {}".format(order_found))
        return order_found

    def buy(self, **kwargs): #market_key, price, amount):
        order = self.market.buy(**kwargs)
        self.account.refresh()
        return order

    def cancel(self, order):
        # cancelling specific order
        try:
            self.market.cancel(order['order']['orderid'], account = self.account)
            return True
        except Exception as e:
            print("Error during cancellation! Order_id: {}".format(order['id']))
            print(e)
            return False

    async def apply(self, **kwargs):
        #transition table, if state changes we need to return a task
        #since only orderbooks are used 
        asks, bids =  self.orderbook
        if self.state == 0:
            conf = {
                'price' : self.state0(asks, bids), 'amount' : self.tsize,
                'returnOrderId' : True,
                'account' : self.account,
                'expiration' : 60
            }
            if self.state ==1:
                order = self.buy(**conf)
                order = await self.open_order
                return order
            else:
                return False

        if self.state == 1:
            #bis, order = entry
            open_order = self.open_order
            conf = self.state1(asks, bids)
            if self.state == 0:
                if self.cancel(open_order):
                    return True #transition from state 1 to state 0 
                else:
                    #exceptoin
                    return False
            else:
                return False 


    def state0(self, asks, bids):
        #
        #asks, bids = entry['asks'], entry['bids']
        price_bid = find_price(bids, getattr(self, 'th'), getattr(self, 'tsize'))
        price_ask = find_price(asks, getattr(self, 'th'), getattr(self, 'tsize'))
        spread_estimated = ((price_ask - price_bid)/price_bid).quantize(CheckSpread.satoshi)
        #print("Strategy: Spread: {}".format(spread_estimated))
        if spread_estimated > self.th:
            self.state = 1
            return price_bid
        elif spread_estimated < 0:
            raise ArbitrageException
        else:
            return 0
            
    def state1(self, bids, order, tradingside = 'buy'):

        if tradingside == 'buy':
            max_deviation = Decimal('0.0000000001') 
        else:
            max_deviation = Decimal('1')

        # Checks if better price exists
        
        estimated_price = find_price(bids, self.th, self.tsize, previous_order=order)
        order_price = order['price'].quantize(CheckSpread.satoshi)

        if abs(estimated_price - order_price) > max_deviation:
            print("Strategy: Order deviation too large")
            self.state = 0
            return False
        else:
            return True
"""


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
"""
