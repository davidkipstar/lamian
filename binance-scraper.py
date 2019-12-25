# download binance orderbooks and trades for new price calculation, where
# volume ~ liquidity
import keyring
import numpy as np
import asyncio
import time 
import datetime
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

from binance.client import Client

def scrape(client):

    try:
        tickers = client.get_all_tickers()
        now = datetime.datetime.now()
        timedelta = now - now
        rate = datetime.timedelta(seconds = 1)

        with open('scrape_test.json', 'w') as f:
            while True:
                if timedelta < rate:
                    #sleep for one milisecond
                    time.sleep(0.001)
                    timedelta = datetime.datetime.now() - now

                else:
                    old = now
                    now = datetime.datetime.now()
                    for ticker in tickers:
                        j = client.get_order_book(symbol = ticker['symbol'])
                        json.dump(j, f)

                    logging.info("all scraped after {old-now}")
                    #update time 
                    timedelta = now - now

    except KeyboardInterrupt:
        print(f"done {now}")

if __name__ == '__main__':
    api_key    = 'qKmOPUFDkIL3eZhLdTKxD5P3cV2rPinqFhnqmpxQrkuWDX4e57Ip86xJWmHak1uF'
    api_secret =  'L33AiLBGqQwfJXnUU7vyvGuXxS1NklGm6NwyHAH73C98DJAFR5iMSeuQxjkypcOb'

    client = Client(api_key, api_secret)
    scrape(client)

