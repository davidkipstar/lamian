from manager import Manager
from manager import Worker
#from worker import Worker
#from strategy import Strategy

"""
basecur, quotecur
cancel orders
assign workers according to spread
node selection for workers
"""

if __name__ == '__main__':

    m = Manager('credentials.json')
    #Strategy()
    m.add_worker('BTC-LGS.json')
    m.add_worker('BTC-LCC.json')
    m.add_worker('LCC-BTC.json')
    m.add_worker('LGS-BTC.json')
    #
    #m.add_strategy()

    #
    m.start()
    print("start finished")
    m.manage()