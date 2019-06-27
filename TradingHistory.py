
import datetime
import time 
from collections import OrderedDict


class TradingHistory:
    #
    def __init__(self, bot, **trades):
        self.error = bot #
        # datetime object : (price, amount)
        self.start = datetime.datetime.now()
        self.history = OrderedDict(trades)
        self.max_len = 100

    @classmethod 
    def from_csv(cls, filename):
        #
        return cls(**history)

    @classmethod 
    def from_trades(cls, trades):
        return cls(trades)

    def export_csv(self, history):
        #
        pass 

    #filter 
    def update(self, trades):
        timestamp = datetime.datetime.now()
        for trade in trades:
            price = trade['price']
            amount = trade['quote'].amount 
            if not self.find_trade(price, amount):
                self.new_trade(trade, timestamp)
        
    #access
    def find_trade(self, price, amount):
        exe_amount = list(map(lambda x: x['quote'].amount, self.history))
        exe_price = list(map(lambda x: x['price'], self.history))
        price_amount_combi = list(zip(exe_amount, exe_price))
        return (amount, price) in price_amount_combi

    #entry
    def new_trade(self, trade, timestamp = datetime.datetime.now()):    
        #unique timing
        self.error("Made Trade {} {} ".format(trade['price'], trade['quote'].amount))
        if timestamp in self.history.keys():
            print("Already know this time, seems like 2 trades :>")
            time.sleep(0.5)
            self.history[datetime.datetime.now()] = trade
        else:
            self.history[timestamp] = trade

        #
        if len(self.history) > self.max_len:
            #export csv 
            self.export_csv(self.history)
            self.history = OrderedDict()