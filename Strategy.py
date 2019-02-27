from utils import find_price
from decimal import Decimal

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
        #input is orde
        price_estimated = find_price(asks, getattr(self, 'th'), getattr(self, 'tsize'))
        
        price = lambda x: +Decimal(x['price']).quantize(CheckSpread.satoshi)
        price_v = bids.apply(price)
        price_bid = price_v[0].quantize(CheckSpread.satoshi)
        
        spread_estimated = ((price_estimated - price_bid)/price_bid).quantize(CheckSpread.satoshi)
        print("Estimated spread: {}".format(spread_estimated))
        if spread_estimated > self.th:
            self.state = 1
            return price_bid
        else:
            return 0
            
    def state1(self, asks, order):
        estimated_price = find_price(asks, 
                                        self.th, 
                                        self.tsize, 
                                        previous_order=order)
        # 5% diviation
        order_price = order['price']
        
        if abs(float(estimated_price) - order_price)/order_price > 0.95:
            self.state = 0 
        else:
            self.state = 1
