
import asyncio
class Edge:

    def __init__(self,*args,**kwargs):

        #IF ONLY ONE NODE IS GIVEN
        #  WE CREATE AN EDGE \
        #  AN AVAILABLE NODE
        
        #HOW DO WE PICK THE STRATEGY?
        self.config = {'th':0.05}
        self.coin = ''
    
    @staticmethod
    async def run(self, strategy):
        try:
            #await asyncio.sleep(1)
            await strategy(self.config)
        except Exception as e:
            print("Exception {} in {} ".format(e, self.coin))