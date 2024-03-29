from utils import find_price, convert_to_quote, convert_to_base, numberlist
from decimal import Decimal
import pandas as pd
import asyncio
import sys
import logging 
import time
import numpy
from bitshares import BitShares
from bitshares.account import Account
from bitshares.market import Market
from arbitrage import ArbitrageException

import re 
class Agent:

    def __init__(self, logger, *args, **kwargs):    
        self.og_tsize = kwargs['tsize'] # only need this for buy atm
        self.logger = logging.getLogger("{}_{}".format(__name__,re.sub('BRIDGE.','', kwargs['market_key'])))

    @property 
    async def orderbook(self):
        try:
            ob = self.market.orderbook(self.orderbooklimit)
            if len(ob['asks']) >= self.orderbooklimit and len(ob['asks']) >= self.orderbooklimit:
                asks, bids = pd.DataFrame(ob['asks']), pd.DataFrame(ob['bids'])
                self.logger.info("orderbook received")
            else: # if connection fails / new bug
                asks, bids = None, None
        except:
            self.logger.info("not liquid.")
            asks, bids = None, None
        await asyncio.sleep(0)
        return asks, bids 

    #get tsize
    @property
    async def tsize(self):
        # Check if balance changed
        try:
            # MUST fetch balance and open orders together!
            # BC if orders are open, the balance will already be subtracted. Only this way we get a full picture.
            self.account.refresh()
            my_coins = self.account.balances
            self.balance = dict(zip(map(lambda x: getattr(x,'symbol'),my_coins),my_coins))
            self.current_open_orders = self.market_open_orders()
                      
            if self.tradingside == 'buy':
                #case btc
                asks, bids = await self.orderbook
                
                # Retrieve sell data for comment above
                # Added in quote_inventory
                sell_orders = list(filter(lambda x: x['for_sale']['symbol'] == self.buy, self.current_open_orders))
                self.quote_inventory_in_sells = sum(list(map(lambda x: x['for_sale']['amount'], sell_orders))) # is min 0

                self.balance_in_quote = convert_to_quote(asks, bids, self.og_tsize)
                self.quote_inventory = self.quote_inventory_in_sells + max(self.balance_in_quote - 0.01, 0) # must exist for lifo, however we subtract some of that in self._tsize again. slightly inefficient, but hotfix.

                # check how much we have on sell side and compensate so that we dont continue to buy if we have sufficient inventory
                # warning: if we have 0 of a coin, then below expression will fail. So buy a little of each coin in advance or change this try-except structure.
                self.inventory = max(self.balance[self.buy].amount - 0.01, 0)

                # All in quote: Planned tsize - balance - balance in sells
                self._tsize = max(self.balance_in_quote - self.inventory - self.quote_inventory_in_sells, 0) # also subtract what we already have in orders! This is done in self.quote_inventory_in_sells

            else:
                try:
                    self.inventory = max(self.balance[self.sell].amount - 0.01, 0)
                    self._tsize = self.inventory
                except:
                    self.inventory = 0
                    self._tsize = self.inventory

            
        # Error can occur when balance of a coin is precisely zero, then it doesnt exist in the balance list. 
        except Exception as e:
            self.logger.info("No balance for {}".format(self.major_coin)) 
            
        finally:
            self.logger.info("balance for {} is {} ".format(self.major_coin, self._tsize))
            return self._tsize

    #change tsize 
    @tsize.setter
    def tsize(self, size):
        self._tsize = size
        #ob[0] = asks, ob[1] = bids

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
                amount = Decimal(kwargs['amount']).quantize(CheckSpread.satoshi)
            # amhttps://www.kicker.de/ount = 0.000002
            if self.market:
                self.market.clear()  # Else fails after first successful order, check: https://github.com/bitshares/python-bitshares/issues/86
                # That issue is NOT fixed obviously
            self.market = Market(self.market_key, instance = self.instance)
            self.market.bitshares.wallet.unlock(self.pw)
            #self.market.bitshares.wallet.addPrivateKey('5KgkgfK4suQqLJY1Uv8mY4tPx4e8V8a2q2SX8xbS5o8UN9rxBJJ')
            #print(self.market_key, ': setting order')
            #print(self.account)
            print('Unlocked?! ', self.account.bitshares.wallet.unlocked())
            print('tradingside: ', self.tradingside)
            #self.account.bitshares.wallet.unlock(self.pw)

            amount = amount - Decimal('0.01')
            if self.tradingside == 'buy':         
                order = self.market.buy(price = price,
                                    amount = amount,
                                    returnOrderId = True,
                                    account = self.account,
                                    expiration = 500)
            else:
                
                order = self.market.sell(price = price,
                                    amount = amount,
                                    returnOrderId = True,
                                    account = self.account,
                                    expiration = 500)
            
            self.logger.info("order placed for {} @ {}".format(amount ,price))
            #self.logger.info('order object {}'.format(order))
            if order:
                self.account.refresh()
                # return[0] = price and return[1] = amount
                # DONT CHANGE THIS
                # Optionally add another index
                # this goes straight to state0 for previous_order, which is then needed in find_price for dropidx!
                return order, price, amount  # actually order object but its annoying to extract price and amount (converted)
        except Exception as e:
            # Try to reconnect if shit fails using from_kwargs:
            instance = BitShares(witness_url = kwargs['url'])
            account = Account(kwargs['acc'], bitshares_instance = instance, full = True)
            account.bitshares.wallet.unlock(kwargs['pw'])
            #doppeltgemoppelt
            market = Market(kwargs['market_key'], block_instance = instance)
            market.bitshares.wallet.unlock(kwargs['pw'])
            kwargs.update({'account' : account, 'instance': instance, 'market' : market})
            raise ValueError('Order failed!', e)

    @property
    async def my_order(self):
        try:
            order_changed = False
            if self._order:
                order = await self.order_still_active(self._order)
                if order:
                    #check price deviation
                    deviation = 0
                    if deviation:
                        self._order = order
                        self.logger.info("order has been changed: {} {}".format(1,2))
                    self.logger.info("order found")
                    return self._order
                else:
                    self.logger.info("order not found, so it has been filled or is gone")
                    return None 
        except Exception as e:
            self._order = None 
            self._price = None
            self._amount = None 
            self.logger.error("Error in getting order: {}".format(e))
            return None 

    @my_order.setter
    def my_order(self, conf):
        try:
            if self._order:
                self.logger.info("overwrite order")
            self._order, self._price, self._amount = self.place_order(**conf)
            self.logger.info("Order placed for {} {}".format(self._price, self._amount))
        except Exception as e:
            self.logger.error(" Error in setting order {}".format(e))
    
    @my_order.deleter
    def my_order(self):
        try:
            if self._order:
                cancelled = self.cancel(self._order)
                if cancelled:
                    self.logger.info("Canceled order in {}".format(self.market_key))
                else:
                    self.logger.info('Couldnt cancel order in {}'.format(self.market_key))
        
            else:
                self.logger.info("Order already deleted")
            self._order = None
            self._price = None
            self._amount = None 
            
        except:
            self.logger.error("during cancel order, maybe it was filled ")

    async def order_still_active(self, order):
        #
        assert(order)
        self.account.refresh()
        open_os = self.account.openorders
        order_found = False
        for open_order in open_os:
            if order['orderid'] == open_order['id']:
                order_found = True
        self.logger.info("Order found is {}".format(order_found))
        return order_found

    def market_open_orders(self):
        return self.market.accountopenorders(self.acc)

    def trades(self):
        try:
            t = self.market.accounttrades(self.acc, limit = 50)
            if len(t):
                if len(self.executed_trades) == 0:
                    for i in range(len(t)):
                        self.executed_trades.append(t[i])
                else:
                    exe_amount = list(map(lambda x: x['quote'].amount, self.executed_trades))
                    exe_price = list(map(lambda x: x['price'], self.executed_trades))
                    for i in range(len(t)):
                            if t[i]['price'] not in exe_price and t[i]['base'].amount not in exe_amount:
                                logging.info("Found trades {}".format(t))
                                self.executed_trades.append(t[i])
                # Prevent memory leak!!
                max_len = 100
                if len(self.executed_trades) > max_len:
                    self.executed_trades = self.executed_trades[(len(self.executed_trades) - max_len):len(self.executed_trades)]
            return t
        except:
            self.logger.info('Couldnt retrieve trades')
            return []

    def cancel(self, order):
        # cancelling specific order
        try:
            self.market.cancel(order['orderid'], account = self.account)
            return True
        except Exception as e:
            print('couldnt cancel!! error: ', e)
            return False

    def calc_avg_price(self, type, recent_trades, lifo = False):

        # type is 'buy' or 'sell'

        try:
            #def m(key,recent_trades):
            #    return list(filter(lambda x: x['type'] == self.tradingside, list(map(lambda x: x[key], recent_trades))))

            # ATTENTION:
            # all trades are classified as 'sell'!!! need to distinguish elsewise.
            # Use price: if price > 1 then we should have a buy
            # if price < 1 it should be a sell
            # to be honest thats a rather shitty but given the circumstances probably the best id


            if type == 'buy':
                filtered_trades = list(filter(lambda x: x['price'] > 1, recent_trades))
            else:
                filtered_trades = list(filter(lambda x: x['price'] < 1, recent_trades))
            
            recent_amount_ele = list(map(lambda x: x['quote'].amount, filtered_trades)) #m('quote', recent_trades)
            recent_rate_ele = list(map(lambda x: x['price'], filtered_trades)) #m('price',recent_trades)

            lista = recent_amount_ele
            listb = recent_rate_ele

            if len(lista) == 0:
                return 0

            if type == 'buy' and lifo:
                print('lifo')
                if self.tradingside == 'buy':
                    # Which kind of inventory we have depends on tsize!
                    curr_inv = max(self.balance[self.buy].amount + self.quote_inventory, 0)
                else:
                    curr_inv = max(self.balance[self.buy].amount + self.inventory, 0)
                if curr_inv > 0:
                    lista.reverse()
                    listb.reverse()
                    lista = lista[:numberlist(lista, curr_inv)]
                    listb = listb[:len(lista)]

            prod = [a*b for a,b in zip(lista,listb)]
            avg_price = sum(prod)/sum(recent_amount_ele)

            # If we have a buy, we must reconvert the price to quote:base
            if type == 'sell':
                return avg_price 
            else:
                return 1/avg_price

        except Exception as e:
            print('Couldnt calculate average price, ', e)
            return 0

    def running_mean(self, N):
        cumsum = numpy.cumsum(numpy.insert(self.spread_history[(len(self.spread_history) - N):len(self.spread_history)], 0, 0))
        return Decimal(0.9) * (cumsum[N:] - cumsum[:-N]) / N # trimmed down to 90% for buy condition

    def calc_avg_spread(self, estimated_spread):
        max_len = 1000
        if self.counter == 0:
            self.spread_history.append(estimated_spread)
        elif self.counter == 10: # reset, only count every tenth iteration for the avg spread
            self.counter = 0
        _N = min(len(self.spread_history), 800)
        if len(self.spread_history) > max_len:
            self.spread_history = self.spread_history[(len(self.spread_history)-_N):len(self.spread_history)]
        avg_spread = self.running_mean(_N)
        return avg_spread

    # This is repeated. Yea thats ugly but its for testing. just exchange the variables later
    # LOOK OUT FOR INFLATED AND DEFLATED STAT!! See buy condition!
    def running_mean_bids(self, N):
        cumsum = numpy.cumsum(numpy.insert(self.bid_history[(len(self.bid_history) - N):len(self.bid_history)], 0, 0))
        return Decimal(1.05) * (cumsum[N:] - cumsum[:-N]) / N # INFLATED111111111

    def calc_avg_bid(self, estimated_bid):
        max_len = 1000
        if self.counter == 0:
            self.bid_history.append(estimated_bid)
        elif self.counter == 10: # reset, only count every tenth iteration for the avg spread
            self.counter = 0
        _N = min(len(self.bid_history), 800)
        if len(self.bid_history) > max_len:
            self.bid_history = self.bid_history[(len(self.bid_history)-_N):len(self.bid_history)]
        avg_bid = self.running_mean_bids(_N)
        return avg_bid


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
        kwargs.update({'og_tsize': kwargs['tsize']})
        super().__init__(logger, **kwargs)
        for key, arg in kwargs.items():
            setattr(self, key, arg)
        
        ob = self.market.orderbook(self.orderbooklimit)
        asks, bids = pd.DataFrame(ob['asks']), pd.DataFrame(ob['bids'])
        self.logger.info("length of asks is {}".format(len(asks)))

        #logger.info("Starting to {} {} of {}".format(self.tradingside,self._tsize, self.major_coin))
        #self.og_tsize = self.tsize # save, will be reduced once having bought
        self.executed_trades = []
        self.current_trades = []
        self.spread_history = []
        self.bid_history = []
        self._order = None 
        self._avg_price = None
        self.counter = 0


    @classmethod
    def from_kwargs(cls, logger, **kwargs):
        instance = BitShares(kwargs['url'])
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
        avg_buy_price_lifo = 0
        
        if asks is None or bids is None:
            self.logger.info('sleeping, no orderbook')
            return asyncio.sleep(10)

        self.current_trades = self.trades()  
        if len(self.current_trades) > 0:
            # Fails first time because tsize doesnt exist yet
            # Need this as lower bound for sell price
            if self.tradingside == 'sell':
                avg_buy_price_lifo = self.calc_avg_price('buy', self.executed_trades, True)




        if self.state == 0:

            # If trades, we need to estimate the tsize reduction
            # amount_spent = Sum over all btc tsizes in trades
            # If tsize < og_tsize, exit
            # amount_spent = max(sum(self.current_trades['amount']), 0)
            # tsize -= amount_spent
            #print('Strategy orders:', self.current_open_orders)
            # self._tsize = await self.tsize
            await self.tsize
            print(self.tradingside, ' : ' ,self._tsize)
            conf = {
                'price' : self.state0(asks, bids, avg_buy_price_lifo), # is already Decimal as returned from state0
                'amount' : self._tsize, # not Decimal yet, to be done when setting order
                'returnOrderId' : True,
                'account' : self.account,
                'expiration' : 60
            }

            if self.state == 1  and not self._order and conf['amount'] > 0.02: # and len(self.current_open_orders) < 3
                self.my_order = conf
            else:
                #push into sleep 
                self.state = 2
            return asyncio.sleep(0.1)
                
        if self.state == 1:
            my_order = await self.my_order
            if my_order:
                if self.tradingside == 'sell':
                    conf = self.state1(asks, my_order, avg_buy_price_lifo, tradingside = 'sell')
                else:
                    conf = self.state1(bids, my_order, avg_buy_price_lifo, tradingside = 'buy')
                if self.state == 0 and my_order is not None: # and len(self.current_open_orders) > 0:
                    del self.my_order
                return asyncio.sleep(0.1)
            else:
                del self.my_order
                self.state = 2 #changed to 2 instead of 0 thus checks balance! 
                return asyncio.sleep(0.1)
        
        if self.state == 2:
            # wenn tsize = 0 und tradignside == 'sell' 
            # in kwargs dann erstmal sleep und anschliessend immer balance testen. wenn > 0.01 dann verkaufen
    
            #min_balance !
            #state2()
            min_balance = 0.021
            await self.tsize
            if self._tsize > min_balance:
                    self.state = 0
            else:
                self.state = 0 #hope we own btc
            return asyncio.sleep(5)
            
    def state0(self, asks, bids, avg_buy_price_lifo):
        #print(self.market, ' : entering state0')
        #asks, bids = entry['asks'], entry['bids']
        #print(self.market_key, ': state0 activated')
        price_bid = find_price(bids, getattr(self, 'ob_th'), getattr(self, '_tsize'), 0, minimum_liquidity=2)
        price_ask = find_price(asks, getattr(self, 'ob_th'), getattr(self, '_tsize'), avg_buy_price_lifo, minimum_liquidity=0)
        if price_bid is None or price_ask is None:
            # case when too illiquid
            self.orderbooklimit += 5
            if self.orderbooklimit > 50:
                self.orderbooklimit = 25
                self.logger.info('reducing orderbooklimit')
                
            return 0
        else:
            price_bid += self.satoshi
            price_ask -= self.satoshi
        spread_estimated = ((price_ask - price_bid)/price_bid).quantize(CheckSpread.satoshi)
        avg_spread = self.calc_avg_spread(spread_estimated)
        avg_bid = self.calc_avg_bid(Decimal(bids.price[0]).quantize(self.satoshi)) # price_bid
        
        # avg_spread and avg_bid are anti-pump-n-dump insurance.
        # hence we do not buy if either the spread spontaneously diminishes or the bid price rises quickly.
        # todo: define 'quickly' inside the functions and integrate the functions.
        if self.tradingside == 'buy' and spread_estimated > self.th and spread_estimated >= avg_spread and price_bid <= avg_bid: 
            # avg_bid is a little inflated so we can stay below, whereas
            # avg_spread is a little deflated so we can stay above.
            # if we use the lifo min price, then the spread can be pretty damn low. So we need a low self.th for the sell side!
            self.state = 1
            self.logger.info("spread met condition")
            return price_bid
        elif self.tradingside == 'sell' and spread_estimated > self.th:
            self.state = 1
            self.logger.info("spread met condition")
            return price_ask
        else:
            self.logger.info("spread too low currently at {}".format(spread_estimated))
            time.sleep(5)
            return 0
            
    def state1(self, bids, order, avg_buy_price_lifo, tradingside = 'buy'):
        #print(self.market, ': entering state1')
        if tradingside == 'buy':
            max_deviation = Decimal('0.00000001')
            # always 0 for lifo price, as this only concerns the sell value.
            # else the spread becomes reeeally narrow such that we would be unable to trade!
            estimated_price = find_price(bids, getattr(self, 'ob_th'), getattr(self, '_tsize'), 0, previous_order=order, previous_amount=self._amount, previous_price=self._price, minimum_liquidity = 2) # self.which_order(order['orderid'])
        else:
            max_deviation = Decimal('0.00000001') #Decimal('1')
            # first argument bids is actually asks as input
            estimated_price = find_price(bids, getattr(self, 'ob_th'), getattr(self, '_tsize'), avg_buy_price_lifo, previous_order=order, previous_amount=self._amount, previous_price=self._price, minimum_liquidity = 0) # self.which_order(order['orderid'])
        if estimated_price is None:
            # case when too illiquid
            self.orderbooklimit += 5
            if self.orderbooklimit > 50:
                self.orderbooklimit = 25
                self.logger.info('reducing orderbooklimit')
                self.state = 0
                
            return False
        else:
            if self.tradingside == 'buy':
                estimated_price += self.satoshi
            else:
                estimated_price -= self.satoshi


        # Checks if better price exists
        
        order_price = self._price.quantize(self.satoshi)

        if abs(estimated_price - order_price) > max_deviation:
            self.logger.info("deviation  {} too large".format(estimated_price - order_price))
            self.state = 0
            return False
        else:
            self.logger.info("observing open order......")
            return True

