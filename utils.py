
from decimal import *

import pandas as pd

def find_price(orderbook, th, tsize, compensate_orders = False , minimum_liquidity=1):
        """
          Computes spread and computes optimal ask/bid
          orderbook is either bids or asks as generated from update

        """
        satoshi = Decimal('0.00000001')
        th = Decimal(th).quantize(satoshi)
        tsize = Decimal(tsize).quantize(satoshi)
    
        price = lambda x: +Decimal(x['price']).quantize(satoshi)
        quote = lambda x: +Decimal(x['quote']['amount']).quantize(satoshi)

        quote_v = orderbook.apply(quote) 
        price_v = orderbook.apply(price)

        obrevenue_v = quote_v * price_v * th # compensate for threshold
        ownrevenue_v = tsize * price_v 
    
        d = {'quote': quote_v, 'price': price_v, 'obrevenue': obrevenue_v, 'ownrevenue': ownrevenue_v}
        df = pd.DataFrame(d)
        
        # In case we already have active orders, account for them
        if(compensate_orders):
            dropidx = (df['price'] == price_before) & (df['quote'] == tsize)
            df = df.drop(df.index[dropidx]) # overwrite
            
        # Get first bound
        df['obrevenue_cumsum'] = df['obrevenue'].cumsum()
        idx = df.index[df['obrevenue_cumsum'] > df['ownrevenue']].tolist()
        opt_price = df['price'][idx[0]]
        opt_price_rounded = opt_price.quantize(satoshi)
       
        # Get second bound if liquidity requirement
        if(minimum_liquidity):
            #safety 
            dfsub = df[(df['price'] <= opt_price)]
            dfsub = dfsub.reset_index()
            dfsub = dfsub.drop('obrevenue_cumsum', axis = 1) # clean up first, just to make sure
            dfsub['obrevenue_cumsum'] = dfsub['obrevenue'].cumsum() # once again reassign
            dfsub['xtimes_ownrevenue'] = dfsub['ownrevenue'] * minimum_liquidity
            lower_bound = dfsub.index[dfsub['obrevenue_cumsum'] > dfsub['xtimes_ownrevenue']].tolist()
            # now this is the lower bound. Combine them to find the optimal price
            opt_price = dfsub['price'][lower_bound[0]]
        
        return opt_price_rounded

def convert_to_quote(asks, bids, btc_tsize=0.01):
    # 
    #
    lowest_ask = asks[0]['price']
    highest_bid = bids[0]['price']
    midprice = 0.5 * (lowest_ask + highest_bid)
    init_bid = btc_tsize/midprice
    
    return init_bid

        