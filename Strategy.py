from utils import find_price
from decimal import Decimal

"""
Strategy:
    - Input: Data (Orderbook, Transaction)
    - Output: State 
Usage:
    #
    Decides if a strategy needs to change or not, does not perform actual changes on the system
    Define States:
        - on input check conditions 
        - return if condition is met or not
    Don't call Manager, Worker from here

"""
class CheckSpread:
    satoshi = Decimal('0.00000001')
        
    def __init__(self, tsize = 0.001, th = 0.01):
        #
        self.tsize = tsize 
        self.th = th
        self.state = 0 
        #self.on('orderbook')
        #self.on('enemy')

    def state0(self, asks, bids):
        
        price_estimated = find_price(asks, getattr(self, 'th'), getattr(self, 'tsize'))
        price = lambda x: +Decimal(x['price']).quantize(CheckSpread.satoshi)
        price_v = bids.apply(price)
        price_bid = price_v[0].quantize(CheckSpread.satoshi)
        
        spread_estimated = ((price_estimated - price_bid)/price_bid).quantize(CheckSpread.satoshi)
        print("Strategy: Spread: {}".format(spread_estimated))
        
        if spread_estimated > self.th:
            self.state = 1
            print("Strategy: Condition met placing order ")
            return price_bid
        else:
            return 0
            
    def state1(self, asks, order):
        # Checks if better price exists
        estimated_price = find_price(asks, 
                                        self.th, 
                                        self.tsize, 
                                        previous_order=order)
        
        #print('estimated_price', estimated_price)
        order_price = order['price'].quantize(CheckSpread.satoshi)
        
        if abs(estimated_price - order_price) > 0.0000000001:
            print("Strategy: Order deviation too large")
            self.state = 0
            return False
        else:
            #print("Strategy: Order placed")
            return True

