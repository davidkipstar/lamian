import telegram 
import numpy as np
import datetime
import asyncio 
import logging 
import os
import time 
#Variables 

class Bot:
    TOKEN = '777999829:AAG-zKO3DU2_UDzyz5e-rSF-tBww9Q82gGw'
    def __init__(self, name, level):        
        self._id = [344197031]
        self.bot = telegram.Bot(token= Bot.TOKEN)

        self.start_time =  datetime.datetime.now()
        log_filename = self.start_time.strftime('%Y-%m-%d') + '{}-{}.log'.format(name, self.__class__.__name__)    
        logger = logging.getLogger(name)
        logger.setLevel(level)
        formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(message)s')
        filename = '/'.join([os.getcwd(),'log',log_filename])
        self.logger = logger
        self.setHandler(filename, level)
    

    def setHandler(self, filename, level):
        #
        self.fh = logging.FileHandler(filename)
        self.fh.setLevel(level)
        self.formatter = logging.Formatter("%(asctime)s : %(levelname)s : %(message)s")
        self.fh.setFormatter(self.formatter)
        self.logger.addHandler(self.fh)    
        self.filename = filename

    def send_file(self):
        #open close filename
        file = self.filename
        self.bot.send_document(chat_id=self._id[0], document=open(file, 'rb'))


class ErrorBot(Bot):
    
    def __init__(self, name):
        self.name = name 
        super().__init__(name, logging.ERROR)
        

    def __call__(self, msg, delta = datetime.timedelta(seconds = 10)):
        self.logger.error(msg)
        self.bot.sendMessage(chat_id = self._id[0], text = msg)
        if  datetime.datetime.now() - self.start_time > delta:
            self.send_file()
            self.logger.removeHandler(self.fh)
            
            self.start_time =  datetime.datetime.now()
            log_filename = self.start_time.strftime('%Y-%m-%d') + '{}-{}.log'.format(self.name, self.__class__.__name__)    
            formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(message)s')
            filename = '/'.join([os.getcwd(),'log',log_filename])
            self.setHandler(filename, logging.ERROR)

class InfoBot(Bot):

    def __init__(self, name):
        super().__init__(name, logging.INFO)
        

    def __call__(self, msg, delta = datetime.timedelta(seconds = 10)):
        self.logger.info(msg)
        #self.bot.sendMessage(chat_id = self._id[0], text = msg)
        if datetime.datetime.now() - self.start_time > delta:
            self.send_file()
            self.logger.removeHandler(self.fh)
            
            self.start_time =  datetime.datetime.now()
            log_filename = self.start_time.strftime('%Y-%m-%d') + '{}.log'.format(self.__class__.__name__)    
            formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(message)s')
            filename = '/'.join([os.getcwd(),'log',log_filename])
            self.setHandler(filename, logging.INFO)
