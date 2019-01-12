import json
import decimal
import pandas as pd

from bitshares import BitShares
from bitshares.account import Account
from bitshares.market import Market


class Statemachine:

    """
      State 1: Checking for order options, calculate tsize_bid/ask. 
      State 2: Set order, scan for fill to reach step 3. Check spread and return to step . Register Id 
      State 3: Order has been filled.        
    """
    _orderids = []
    _workers = []
    def __init__(self, pwd, account_str,side ,**kwargs):
        #side = True is buy, side = False is sell
        self.instance = BitShares()    
        self.instance.wallet.unlock(pwd)
        if self.instance.wallet.unlocked():
            print("Unlocking wallet was successfull")
        else:
            print("Unlocking wallet was not successfull")
        self.acc = Account(account_str,bitshares_instance=self.instance, full = True)

        if side:
            self.opposite_side = (kwargs['start_tsize_ask'],kwargs['th_ask'])
        else:
            self.opposite_side = (kwargs['start_tsize_bid'],kwargs['th_bid'])
        self.state = None
        self.side = side
        self.orderid = None  

        #asign kwargs  
        for key,value in kwargs.items():
            setattr(self,key,value)
    
    def run(self):
        self.get_state().run()

    def update(self)
        """
            Process orderbook:

        """
   
        orderbook_df = pd.DataFrame(self.market.orderbook(self.orderbooklimit))
    
        asks = orderbook_df['asks'] # prices increasing from index 0 to index 1
        bids = orderbook_df['bids'] # prices decreasing from index 0 to index 1
        return asks,bids 
    
    def find_price(self, compensate_orders, minimum_liquidity=0 ):
        """
          Computes spread and computes optimal ask/bid

        """
        satoshi = Decimal('0.00000001')
        th = Decimal(self.th).quantize(satoshi)
        tsize = Decimal(self.tsize).quantize(satoshi)
    
        price = lambda x: +Decimal(x['price']).quantize(satoshi)
        quote = lambda x: +Decimal(x['quote']['amount']).quantize(satoshi)

        quote_v = orderbook.apply(quote) 
        price_v = orderbook.apply(price)

        obrevenue_v = quote_v * price_v * self.th # compensate for threshold
        ownrevenue_v = tsize * price_v 
    
        d = {'quote': quote_v, 'price': price_v, 'obrevenue': obrevenue_v, 'ownrevenue': ownrevenue_v}
        df = pd.DataFrame(d)
        df['obrevenue_cumsum'] = df['obrevenue'].cumsum()
        idx = df.index[df['obrevenue_cumsum'] > df['ownrevenue']].tolist()
        opt_price = df['price'][idx[0]]
        opt_price_rounded = opt_price.quantize(satoshi)
        return opt_price_rounded


    def state1(self):
        #
        up = self.update()
        price = self.find_price([])
        print("Optimal price @ {}".format(price))
        price2 = self.find_price()

        
    return d
    
        up = update(market, th_bid, th_ask, tsize_bid, tsize_ask)
        test_ask = check_spread(up['asks'], th_ask, init_tsize_ask)
        test_bid = check_spread(up['bids'], th_bid, init_tsize_bid)
        spread = (test_ask - test_bid)/test_bid
        spread = spread.quantize(satoshi)
            print('Spread: {:_<5f}'.format(spread))
            
    
            all_open_orders = len(get_open_orders(market, acc))
            balance_basecur, balance_quotecur = accountbalance(acc, quotecur, basecur, tsize_bid, tsize_ask)
            
            # Dynamic tsizes
            if(balance_basecur > 0.01):
                init_tsize_bid = init_bid_size(0.01, market)
            else:
                init_tsize_bid = 0
                
                
    
            # Buy until max is reached
            if(balance_quotecur >= 0 and balance_quotecur < max_tsize_ask):
                tsize_bid = init_tsize_bid
                
                if(balance_quotecur > 1):
                    # Activate selling
                    tsize_ask = min(balance_quotecur - 0.01, init_tsize_bid)
                    
                    # Wenn gerade Kaufsorder gecancelt wurde und noch eine offen ist, dann muss dies eine Verkaufsorder sein
                    # Also nicht neu setzen. 
                    if(buy_cancelled == True and all_open_orders == 1):
                        sell_cancelled = False
                        
                    else:
                        sell_cancelled = True
                else:
                    tsize_ask = 0
                    cancel_all_orders(market, account_str)
                    max_orders = 1
                    print('max_orders = ', max_orders)
                print('condition1')
                print('tsize_ask:', tsize_ask)
                
            # If we have reached the limit, stop buying and sell instead
            elif(balance_quotecur >= max_tsize_ask):
                # Deactivate Buying
                # Activate Selling only
                tsize_bid = 0 
                tsize_ask = min(balance_quotecur - 0.01, init_tsize_bid)
                buy_cancelled = False
                sell_cancelled = True # activate selling
                print('tsize_ask:', tsize_ask)
                print('condition2')
            
            
            # If we can't get a nice spread on the bid side then set tsize_bid to zero
            # to avoid buying for shitty prices
            if(spread < spread_th):
                tsize_bid = 0
                print('Shitty spread, not buying atm')
    
    
            if(tsize_bid > 0 and tsize_ask > 0):
                soll_orders = 2
            elif(tsize_bid > 0 and tsize_ask == 0):
                soll_orders = 1
            elif(tsize_bid < 0 and tsize_ask == 0):
                soll_orders = 1
            elif(tsize_bid == 0 and tsize_ask > 0):
                soll_orders = 1
            elif(tsize_bid == 0 and tsize_ask == 0):
                soll_orders = 0
                # This implicitly handles the if spread > spread_th stuff. 
                # We justt reset tsize_bid to zero (as above) if no juicy spread
                
                time.sleep(10)
                print('neither buying nor selling, going to sleep for a while...')
                break; # back to fetching info
            else:
                print('this shouldnt happen!!!')
                break;
    
    
            

     
if __name__ == '__main__':
    maker = MarketMaker( #'BTC-LCC.json',
                '5KgkgfK4suQqLJY1Uv8mY4tPx4e8V8a2q2SX8xbS5o8UN9rxBJJ',
                'kipstar1337')
    maker.join('BTC-LCC.json')
    maker.join('BTC-LGS.json')
    #maker.run()
    