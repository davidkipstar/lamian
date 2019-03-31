class ArbitrageException(Exception):
    def __init___(self,dErrorArguments):
        Exception.__init__(self,"Arbitrage on {0}".format(dErrorArguments))
        self.dErrorArguments = dErrorArguments
 