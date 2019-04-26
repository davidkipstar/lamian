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

    def order_filled(self, w_order, market_string):
        order_was_filled = False
        recent_trades = self.new_trade(market_string)
        if recent_trades:
            order_was_filled = True
        return order_was_filled, recent_trades

    @property
    def open_orders(self):
        self.account.refresh()
        #mkt = self.get_market(self.market_string)
        open_orders = self.account.openorders
        #market_open_orders = mkt.accountopenorders(account = self.account)
        return open_orders

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

    def order_active(self, order, market_string):
        #print("Manager-orders")
        order_found = False
        open_orders = self.open_orders
        for morder in open_orders:
            #print("Comparing {} with {}".format(morder['id'], order['order']['orderid']))
            if morder['id'] == order['order']['orderid']: 
                order_found = True
        print("Order found: {}".format(order_found))
        return order_found

    def buy(self, market_key, price, amount):
        market = self.get_market(market_key)
        order = market.buy(price = price,
                            amount = amount,
                            returnOrderId = True,
                            account = self.account,
                            expiration = 60)
        self.account.refresh()
        return order

    def cancel(self, order, market_key):
        # cancelling specific order
        try:
            market = self.get_market(market_key)
            market.cancel(order['order']['orderid'], account = self.account)
            return True
        except Exception as e:
            print("Error during cancellation! Order_id: {}".format(order['id']))
            print(e)
            return False

    def cancel_all_orders(self, market_key, order_list = None):
        """
        So far this function cancels all orders for a specific market.
        However, it is desirable to manually pass a list of orderids that are supposed to be cancelled.
        This is currently under construction as we also need to manually pass the markets OR retrieve them
        via their asset id from the order
        """
        if not order_list:

            # Create list of orders to be cancelled, depending on a specific market
            # TODO we are actually signing up twice in the same market because get_market_open_orders requires a market too
            market = self.get_market(market_key)
            orders = self.open_orders
            print((len(orders), 'open orders to cancel'))
            if len(orders):
                attempt = 1
                order_list = []
                for order in orders:
                    order_list.append(order['id'])

            while attempt:
                try:
                    details = market.cancel(order_list, account  = self.account)
                    print(details)
                    attempt = 0
                    return True
                except:
                    print((attempt, 'cancel failed', order_list))
                    attempt += 1
                    if attempt > 3:
                        print('cancel aborted')
                        return False
                    pass

    def get_orderbook(self,market_string):
        try:
            market = self.get_market(market_string)
            orderbook_df = pd.DataFrame(market.orderbook(self.orderbooklimit)) # 
            
            asks = orderbook_df['asks'] # prices increasing from index 0 to index 1
            bids = orderbook_df['bids'] # prices decreasing from index 0 to index 1
            
            return asks,bids 
        
        except Exception as e:
            
            print("Update failed, market is too illiquid: {}".format(e))
            return None, None       

    def get_market(self, market_key):
        if market_key in Manager.markets.keys():
            return Manager.markets[market_key]
        else:
            market = Market(market_key, blockchain_instance = Manager.instance)
            market.bitshares.wallet.unlock(self.pw)
            Manager.markets[market_key] = market
            print("Joined market {}".format(market_key))
            return Manager.markets[market_key]


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

