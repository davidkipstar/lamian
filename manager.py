import json

from bitshares import BitShares
from bitshares.account import Account
from bitshares.market import Market

from multiprocessing import Queue, Process


class Manager:
    _currencies = {}
    
    def __init__(self):
        self.instance = BitShares()   
        self.q = Queue()
    
    def add_worker(self,filename):
        w = Worker(filename)
        if w.credentials['base_cur'] in Manager._currencies.keys():
            Manager._currencies[w.credentials['base_cur']] = Manager._currencies[w.credentials['base_cur']].appned(w)
        else:
            Manager._currencies[w.credentials['base_cur']] = [w]
    
    def run(self):
        #start each worker
        #manage
        self.manage()
    def manage(self):
        #queue
        while True:
            x = self.q.get()
            #got signal from 
            #filter state 
            #apply strategy
            #continue or adjust
            print(x)

class Worker(Manager):

    def __init__(self,filename):
        super().__init__()
        self.credentials()
        self.settings(filename)
        self.state = None

    def credentials(self):
        try:
            #load settings and unlock wallet
            with open('credentials.json') as f:
                j = json.load(f)
                setattr(self,'credentials',j)
            #unlock
            self.instance.wallet.unlock(self.credentials['pw'])
            if self.instance.wallet.unlocked():
                print("Unlocking wallet was successfull")
                self.acc = Account(self.credentials['acc'], bitshares_instance=self.instance, full = True)
            else:
                raise ValueError("Unlocking not succesfull, check credentials.json")
        except Exception as e:
            print("Error {}".format(e))

    def settings(self, filename):
        # pose boundary on settings here if wanted
        with open(filename) as f:
            j = json.load(f)
            setattr(self,'settings',j)
        
        #register to global Manager
        if j['basecur'] in Manager._currencies.keys():
            super()._currencies[j['basecur']].append(self)
        else:
            super()._currencies[j['basecur']] = [self]

    

    def run(self,method):
        try:
            while 
        


if __name__ == '__main__':
    #setup Manager
    m = Manager()
    m.add_worker('BTC-LGS.json')
    m.add_worker('BTC-LCC.json')

    #run
    m. 

    print(m._currencies)