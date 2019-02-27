
from decimal import *

import pandas as pd


def find_price(orderbook, th, tsize, previous_order=None, minimum_liquidity=1):
    """
      Computes spread and computes optimal ask/bid
      orderbook is either bids or asks as generated from update

    """
    satoshi = Decimal('0.00000001')
    th = Decimal(th).quantize(satoshi)
    tsize = Decimal(tsize).quantize(satoshi)

    def price(x): return +Decimal(x['price']).quantize(satoshi)
    def quote(x): return +Decimal(x['quote']['amount']).quantize(satoshi)

    quote_v = orderbook.apply(quote)
    price_v = orderbook.apply(price)

    obrevenue_v = quote_v * price_v * th  # compensate for threshold
    ownrevenue_v = tsize * price_v

    d = {'quote': quote_v, 'price': price_v,
         'obrevenue': obrevenue_v, 'ownrevenue': ownrevenue_v}
    df = pd.DataFrame(d)
    opt_price_rounded = 0

    # In case we already have active orders, account for them
    if previous_order:
        dropidx = (df['price'] == previous_order['price']) & (df['quote'] == previous_order['amount'])
        df = df.drop(df.index[dropidx])  # overwrite

    # Get first bound
    df['obrevenue_cumsum'] = df['obrevenue'].cumsum()
    idx = df.index[df['obrevenue_cumsum'] > df['ownrevenue']].tolist()
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
        lower_bound = dfsub.index[dfsub['obrevenue_cumsum']
                                > dfsub['xtimes_ownrevenue']].tolist()
        # now this is the lower bound. Combine them to find the optimal price
        opt_price = dfsub['price'][lower_bound[0]]

    return opt_price_rounded


def convert_to_quote(asks, bids, basecur_amount):  # btc_tsize = basecur amount
    #
    #
    lowest_ask = asks[0]['price']
    highest_bid = bids[0]['price']
    midprice = 0.5 * (lowest_ask + highest_bid)
    init_bid = basecur_amount/midprice

    return init_bid
