import json
import time 
import pandas as pd
import numpy as np
import sys
import asyncio
from asyncio import Queue

from bitshares import BitShares
from bitshares.account import Account
from bitshares.market import Market

from Strategy import CheckSpread
from utils import *

class Manager:
    managers = {}
    def __init__(self, loop, **kwargs):
        for key, item in kwargs.items():
            setattr(self, key, item)
        
        #
        """
        if tradingside == 'buy':
            self.quote = buy
            self.base = sell
        else:
            self.quote = sell
            self.base = buy
        """
        if self.buy not in Manager.managers:
            Manager.managers[self.buy] = []
        
    async def run(self):
        i = 0
        await asyncio.sleep(5)     
        while True:
            #await asyncio.sleep(2) 
            #entry = await queue.get()
            queues = Manager.managers[self.buy]
            print(await asyncio.wait(queues, return_when = asyncio.FIRST_COMPLETED))
            await asyncio.sleep(1)


        
