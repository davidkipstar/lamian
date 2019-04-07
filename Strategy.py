from utils import find_price
from decimal import Decimal

from arbitrage import ArbitrageException

class MarketStrategy:
    
    def __init__(self):
        self.name = 'hi'

class CheckSpread:
    satoshi = Decimal('0.00000001')        
    
    def __init__(self, tsize = 0.001, th = 0.01):
        self.tsize = tsize 
        self.th = th
        self.state = 0

    def state0(self, asks, bids):

        price_bid = find_price(bids, getattr(self, 'th'), getattr(self, 'tsize'))
        price_ask = find_price(asks, getattr(self, 'th'), getattr(self, 'tsize'))

        spread_estimated = ((price_ask - price_bid)/price_bid).quantize(CheckSpread.satoshi)
        print("Strategy: Spread: {}".format(spread_estimated))
        
        if spread_estimated > self.th:
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
            return False
        else:
            return True

