import os 
import time 


from manager import Worker
from manager import Manager

if __name__ == '__main__':

    m = Manager('credentials.json')
    SELLING = Manager._balances.keys()
    BUYING = []
    directory = os.listdir(os.getcwd())
    
    try:
        while len(BUY_COIN) and len(SELL_COIN):
            pairs = [(x,y) for x in BUY_COIN for y in SELL_COIN]    
            
            for buy, sell in pairs:
                f_name = '-'.join([,sell])+'.json' 
                if f_name in directory:
                    m.add_worker(f_name, tsize=tsizes[buy])
                    print("Send worker with {} {} to buy some {}".format())
            m.start()
            tsizes = m.compute_table(pairs)
            NEW_SELL_COIN = m.compare(SELL_COIN, **tsizes)
            time.sleep(20)
            if 'BRIDGE.BTC' in NEW_SELL_COIN:
                pass 
            else:
                SELL_COIN.extend(NEW_SELL_COIN)
                print("Selling coins: ",SELL_COIN)


    except Exception as e:
        print("Error {}".format(e))
