import logging
import os

from ThroughputAnlfService import ThroughputAnlfService

log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=getattr(logging, log_level), format='%(asctime)s - %(levelname)s - %(message)s')

if __name__ == '__main__':
    ThroughputAnlfService().run()
