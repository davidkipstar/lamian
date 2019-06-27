import logging
import sys 
logging.root.handlers = []
logger = logging.Logger(__name__)

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO , filename='{}.log'.format(__name__))

# set up logging to console
console = logging.StreamHandler(sys.stdout)
console.setLevel(logging.ERROR)
# set a format which is simpler for console use
formatter = logging.Formatter('%(asctime)s :  %(name)s : %(levelname)s : %(message)s')
console.setFormatter(formatter)
logging.getLogger().addHandler(console)
logging.Formatter()

logging.debug('debug')
logging.info('info')
logging.warning('warning')
logging.error('error')
logging.exception('exp')