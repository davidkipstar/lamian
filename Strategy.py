from utils import find_price
from decimal import Decimal

from arbitrage import ArbitrageException

class CheckSpread:
    satoshi = Decimal('0.00000001')        
    
    def __init__(self, **kwargs)
        for key, arg in kwargs.items():
            setattr(self, key, arg)
    
        if toQuote:
            asks, bids = self.orderbook
            self.tsize = convert_to_quote(asks, bids, tsize)
            self.cur = quote
        else:
            self.cur = base


    @property 
    async def orderbook(self):
        ob = self.market.orderbook(self.orderbooklimit)
        if len(ob['asks']) != len(ob['bids']) or len(ob['asks']) < self.orderbooklimit:
            asks, bids = pd.DataFrame(ob['asks']), pd.DataFrame(ob['bids'])
            return asks, bids 
        else:
            print("not liquid")
            return None

    
    @property
    async def open_orders(self):
        self.account.refresh()
        open_orders = self.account.openorders
        return open_orders
    
    def apply(self, asks, bids, **kwargs):
        #transition table, if state changes we need to return a task
        #since only orderbooks are used 
        
        if self.state == 0:
            conf = {'price' : self.state0(asks, bids), 'amount' : self.tsize}
            if self.state ==1:
                order = self.buy(**conf)
                self.open_order = order
                return order
            else:
                return False

        if self.state == 1:
            #bis, order = entry
            open_order = self.open_order
            conf = self.state1(asks, bids)
            if self.state == 0:
                self.cancel(open_order)
                return True #transition from state 1 to state 0 
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

