from utils import find_price, convert_to_quote
from decimal import Decimal
import pandas as pd
import asyncio
import sys
import logging 
from bitshares import BitShares
from bitshares.account import Account
from bitshares.market import Market
from arbitrage import ArbitrageException

import re 
class Agent:

    def __init__(self, logger, *args, **kwargs):
        """
        self.logger = self.logger.getLogger()
        self.c_handler = self.logger.StreamHandler(sys.stdout)
        c_format = self.logger.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.c_handler.setFormatter(c_format)
        """
        self.logger = logging.getLogger("{}_{}".format(__name__,re.sub('BRIDGE.','', kwargs['market_key'])))
        pass

    @property 
    async def orderbook(self):
        ob = self.market.orderbook(self.orderbooklimit)
        if len(ob['asks']) >= self.orderbooklimit and len(ob['asks']) >= self.orderbooklimit:
            asks, bids = pd.DataFrame(ob['asks']), pd.DataFrame(ob['bids'])
            self.logger.info("orderbook received")
        else:
            self.logger.info("not liquid.")
            asks, bids = None, None 
        await asyncio.sleep(0)
        return asks, bids 


    @property
    async def open_orders(self):
        self.account.refresh()
        open_os = self.account.openorders
        await asyncio.sleep(0)
        return open_os

    async def which_order(self, order):
        # input order is orderid, string
        #print("Manager-orders")
        order_found = False
        open_orders = await self.open_orders
        full_order_l = []
        for morder in open_orders:
            #print("Comparing {} with {}".format(morder['id'], order['order']['orderid']))
            if morder['id'] == order['orderid']:
                full_order_l.append(order['orderid'])
        self.logger.info("Order found")
        #print("Order found: {}".format(order_found))
        return full_order_l

    def place_order(self, **kwargs):
        try:
            if kwargs:
                # price and amount must both be Decimal here!
                price = kwargs['price'] # already Decimal bc of state0
                amount = Decimal(kwargs['amount'].amount).quantize(CheckSpread.satoshi)
            # amount = 0.000002
            self.market = Market(self.market_key)
            self.market.bitshares.wallet.unlock(self.pw)
            #self.market.bitshares.wallet.addPrivateKey(self.pw)
            #print(self.market_key, ': setting order')
            #print(self.account)
            #print(self.account.bitshares.wallet.unlocked())
            self.account.bitshares.wallet.unlock(self.pw)
            order = self.market.buy(price = price,
                                amount = amount,
                                returnOrderId = True,
                                account = self.account,
                                expiration = 120)
            
            self.logger.info("order placed for {} @ {}".format(amount ,price))
            if order:
                self.account.refresh()
                return order  # actually order object but its annoying to extract price and amount (converted)
        except Exception as e:
            logging.error(e)
            raise ValueError('Order failed!')

    @property
    async def my_order(self):
        order = await self.order_still_active(self._order)
        if order:
            return self._order, True
        else:
            return self._order, False

    @my_order.setter
    def my_order(self, conf):
        self._order = self.place_order(**conf)

    
    @my_order.deleter
    def my_order(self):
        try:
            self.cancel(self._order)
            self._order = None
        except:
            self.logger.error("during cancel order, maybe it was filled ")

    async def order_still_active(self, order):
        #
        self.account.refresh()
        open_os = self.account.openorders
        order_found = False
        for open_order in open_os:
            if order['orderid'] == open_order['id']:
                order_found = True
        return order_found

    def market_open_orders(self):
        return self.market.accountopenorders(self.acc)

    def trades(self):
        t = self.market.accounttrades(self.acc, currencyPair = self.market_key, limit = 50)
        self.executed_trades.append(t)
        return t

    def cancel(self, order):
        # cancelling specific order
        try:
            self.market.cancel(order['order']['orderid'], account = self.account)
            return True
        except Exception as e:
            return False



class CheckSpread(Agent):
    satoshi = Decimal('0.00000001')        
    """
        market: market
        tsize : tsize
        tradingside: 
        toQuote:
        account: account

    """
    def __init__(self,logger, **kwargs):
        super().__init__(logger, **kwargs)
        for key, arg in kwargs.items():
            setattr(self, key, arg)
        ob = self.market.orderbook(self.orderbooklimit)
        asks, bids = pd.DataFrame(ob['asks']), pd.DataFrame(ob['bids'])
        self.logger.info("length of asks is {}".format(len(asks)))    
        if kwargs['toQuote']:
            self.tsize = convert_to_quote(asks, bids, self.tsize)
        self.og_tsize = self.tsize # save, will be reduced once having bought
        self.executed_trades = []

    @classmethod
    def from_kwargs(cls, logger, **kwargs):
        instance = BitShares(witness_url = kwargs['url'])
        account = Account(kwargs['acc'], bitshares_instance = instance, full = True)
        account.bitshares.wallet.unlock(kwargs['pw'])
        #doppeltgemoppelt
        market = Market(kwargs['market_key'], block_instance = instance)
        market.bitshares.wallet.unlock(kwargs['pw'])
        kwargs.update({'account' : account, 'instance': instance, 'market' : market})
        return cls(logger, **kwargs)

    async def apply(self, **kwargs):
        #transition table, if state changes we need to return a task
        #since only orderbooks are used 
        asks, bids = await self.orderbook
        if self.state == 0:
            # Fetch news
            self.current_open_orders = self.market_open_orders()
            self.current_trades = self.trades() # Todo: 
            # If trades, we need to estimate the tsize reduction
            # amount_spent = Sum over all btc tsizes in trades
            # If tsize < og_tsize, exit
            # amount_spent = max(sum(self.current_trades['amount']), 0)
            # tsize -= amount_spent
            print('Strategy orders:', self.current_open_orders)


            conf = {
                'price' : self.state0(asks, bids), # is already Decimal as returned from state0
                'amount' : self.tsize, # not Decimal yet, to be done when setting order
                'returnOrderId' : True,
                'account' : self.account,
                'expiration' : 60
            }
            if self.state == 1 and len(self.current_open_orders) < 2:
                self.my_order = conf
                return await self.my_order
            else:
                #sleep for 5 seconds
                return await asyncio.sleep(5)
                
        if self.state == 1:
            my_order, active = await self.my_order
            if active:
                if self.tradingside == 'sell':
                    conf = self.state1(asks, my_order)
                else:
                    conf = self.state1(bids, my_order)
                if self.state == 0 and my_order: # and len(self.current_open_orders) > 0:
                    del self.my_order
                    logging.info("order delted")
                await asyncio.sleep(0)
                return False
            else:
                logging.info("order not found")
                #assume filled by hund
                
                self.state = 0 
                await asyncio.sleep(0)
                return False
            

    def state0(self, asks, bids):
        #
        #asks, bids = entry['asks'], entry['bids']
        #print(self.market_key, ': state0 activated')
        price_bid = find_price(bids, getattr(self, 'th'), getattr(self, 'tsize'))
        price_ask = find_price(asks, getattr(self, 'th'), getattr(self, 'tsize'))
        spread_estimated = ((price_ask - price_bid)/price_bid).quantize(CheckSpread.satoshi)
        #print("Strategy: Spread: {}".format(spread_estimated))
        if spread_estimated > self.th:
            self.state = 1
            self.logger.info("spread met condition")
            return price_bid
        elif spread_estimated < 0:
            self.logger.warning("arbitrage")
            raise ArbitrageException
        else:
            return 0
            
    def state1(self, bids, order, tradingside = 'buy'):

        if tradingside == 'buy':
            max_deviation = Decimal('0.0000000001') 
        else:
            max_deviation = Decimal('1')

        # Checks if better price exists
        estimated_price = find_price(bids, self.th, self.tsize, previous_order=order)  # self.which_order(order['orderid'])
        order_price = order[0].quantize(CheckSpread.satoshi)

        if abs(estimated_price - order_price) > max_deviation:
            self.logger.warning("deviation too large")
            self.state = 0
            return False
        else:
            return True