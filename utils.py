
from decimal import *

import pandas as pd

from datetime import date, datetime

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))

def find_price(orderbook, ob_th, tsize, previous_order = None, previous_amount = None, previous_price = None, minimum_liquidity=1):
    """
    # INPUT:
        orderbook as Dataframe

      Computes spread and computes optimal ask/bid
      orderbook is either bids or asks as generated from update
        minimum liquididty (maybe at least 1 btc in ob?)
    """
    satoshi = Decimal('0.00000001')
    ob_th = Decimal(ob_th).quantize(satoshi)
    tsize = Decimal(tsize['amount']).quantize(satoshi)

    quote_v = []
    price_v = []
    for i in range(0, len(orderbook) - 1):
        q = orderbook.quote[i].amount
        p = orderbook.price[i]
        quote_v.append(Decimal(q).quantize(satoshi))
        price_v.append(Decimal(p).quantize(satoshi))

        #quote_v.append(Decimal(orderbook.quote[0].amount)).quantize(satoshi)
        #price_v.append(Decimal(orderbook.price[0])).quantize(satoshi)

    """
    def p(x): return +Decimal(x.loc['price']).quantize(satoshi)
    def bal(x): return +Decimal(x.loc['amount']).quantize(satoshi)
    #
    quote_v = orderbook['quote'].copy()
    quote_v = quote_v.apply(bal)
    price_v = orderbook.apply(p)
    """

    obrevenue_v = [a*b*ob_th for a,b in zip(quote_v, price_v)]  # compensate for threshold
    ownrevenue_v = [tsize * p for p in price_v]

    d = {'quote': quote_v, 'price': price_v, 'obrevenue': obrevenue_v, 'ownrevenue': ownrevenue_v}
    df = pd.DataFrame(d)
    opt_price_rounded = 0
    
    # In case we already have active orders, account for them
    if previous_order: # need price and quote of the previous order here in Decimal().quantize(satoshi)
        # Cut off a digit from df['quote'] as it is not exact!
        satoshi_reduced = '0.0000001'
        quote_reduced = []
        for i in range(len(quote_v)):
            a = quote_v[i].quantize(Decimal(satoshi_reduced))
            quote_reduced.append(a)
        df['quote_reduced'] = quote_reduced
        dropidx = (df['price'] == Decimal(previous_price).quantize(satoshi)) & (df['quote_reduced'] == Decimal(previous_amount).quantize(Decimal(satoshi_reduced)))  # right side is not decimal!!
        #dropidx = (df['price'] == Decimal(previous_amount).quantize(satoshi)) & (pd.DataFrame(quote_reduced) == Decimal(previous_price).quantize(Decimal(satoshi_reduced)))
        if len(dropidx) > 0:
            df = df.drop(df.index[dropidx])  # overwrite
        else:
            print('CRITICAL fucking error: Dropidx doesnt exist!')

    # Get first bound
    df['obrevenue_cumsum'] = df['obrevenue'].cumsum()
    idx = df.index[df['obrevenue_cumsum'] > df['ownrevenue']].tolist()
    if len(idx) == 0:
        raise ValueError('Market is waaaay too illiquid')
    opt_price = df['price'][idx[0]]
    opt_price_rounded = opt_price.quantize(satoshi)

    # Get second bound if liquidity requirement
    if(minimum_liquidity):
        # safety
        dfsub = df[(df['price'] <= opt_price)]
        dfsub = dfsub.reset_index()
        # clean up first, just to make sure
        dfsub = dfsub.drop('obrevenue_cumsum', axis=1)
        # once again reassign
        dfsub['obrevenue_cumsum'] = dfsub['obrevenue'].cumsum()
        dfsub['xtimes_ownrevenue'] = dfsub['ownrevenue'] * minimum_liquidity
        lower_bound = dfsub.index[dfsub['obrevenue_cumsum'] > dfsub['xtimes_ownrevenue']].tolist()
        # now this is the lower bound. Combine them to find the optimal price
        opt_price = dfsub['price'][lower_bound[0]]
    #print("Own revenue: {}".format(ownrevenue_v))
    #print("opt : {} , rounded: {}".format(opt_price, opt_price_rounded))
    return opt_price_rounded


def convert_to_quote(asks, bids, basecur_amount):  # btc_tsize = basecur amount
    #

    lowest_ask = asks.iloc[0]['price']
    highest_bid = bids.iloc[0]['price']
    midprice = 0.5 * (lowest_ask + highest_bid)
    init_bid = basecur_amount/midprice
    return init_bid

def convert_to_base(asks, bids, quotecur_amount):  # btc_tsize = basecur amount
    #
    #
    lowest_ask = asks[0]['price']
    highest_bid = bids[0]['price']
    midprice = 0.5 * (lowest_ask + highest_bid)
    init_bid = quotecur_amount * midprice

    return init_bid

def calc_avg_price(recent_trades, tradingside):


    def m(key,recent_trades):
        return list(filter(lambda x: x['type'] == tradingside,list(map(lambda x: x[key], recent_trades))))

    recent_amount_ele = m('amount', recent_trades)
    recent_rate_ele = m('rate',recent_trades)

    lista = recent_amount_ele
    listb = recent_rate_ele

    return [a*b for a,b in zip(lista,listb)]

"""
    def check_balance(self, quote, base, market_string, tradingside):
        # decide if  
        market = self.get_market(market_string)
        _balances = self.balance()
        recent_trades = []
        print("Recent trades: ")
        for trade in market.accounttrades(account=self.account):
            if trade not in self.history:
                print("New Trade found {}".format(trade))
                recent_trades.append(trade)
            else:
                print("Recent trade: {}".format(trade))

        if recent_trades:
            #filled?
            self.history.extend(recent_trades)
            avg_price = calc_avg_price(recent_trades, tradingside)
        
        if tradingside == 'buy':
            if quote in _balances.keys():
                coinbalance = _balances[quote]
            else:
                coinbalance = 0    
        else:
            if base in _balances.keys():
                coinbalance = _balances[base]
        tsize = min(coinbalance - 0.00000001, 0)
        
        return tsize, avg_price

"""