#main.py
import asyncio
import numpy as np
from Node import Node
from Edge import Edge

async def strategy(config):
    print(config)
    return np.random.randint(10)

async def main(settings):
    #args are old tasks 
    tasks = []
    print(settings)
    global strategy
    if 'observe_coins' in settings.keys():
        for coin in settings['observe_coins']:
            coin1 = Node(coin)
            print("Observing {} ...".format(coin))
            if 'trade_coins' in settings.keys():
                for other_coin in settings['trade_coins']:
                    coin2 = Node(other_coin)
                    connection = Edge(coin1, coin2)
                    print("Trading {} ...".format(other_coin))
                    tasks.append(connection)
    print("Starting now ..")
    done, pending = await asyncio.wait([t.run(t, strategy) for t in tasks], return_when=asyncio.FIRST_EXCEPTION)
    print("Done ",done)
    print("Pending",pending)

if __name__ == '__main__':
    #setup all tasks and run
    d = {'observe_coins' : ['BRIDGE.LCC'],
        'trade_coins': ['BRIDGE.BTC']}
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main(d))
    finally:
        loop.close()