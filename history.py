import axe.util as Util
import os
from time import sleep
from datetime import datetime
import sys
import signal
from logging.handlers import TimedRotatingFileHandler
import logging

MAX_COUNT = os.getenv('API_HISTORY_MAX', 1440)
SLEEP_DURATION = os.getenv('API_HISTORY_DURATION', 60)

log_handler = TimedRotatingFileHandler("logs/history.log", "midnight", 1)
log_handler.suffix = "%Y%m%d"
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_handler.setFormatter(log_formatter)
logger = logging.getLogger('history service')
logger.addHandler(log_handler)
logger.setLevel(logging.INFO)


HISTORY_FILE = 'history.json'

def get_reading():
    clamp = lambda n, minn, maxn: max(min(maxn, n), minn)
    data = Util.Htu21.read()
    temperatures = Util.Format.temperatures(Util.Convert.temperature(data['temp_c']))
    humidity = Util.Format.humidity(data['temp_c'], clamp(data['humidity_relative'], 0, 100))
    logger.info("HTU21: read .... temp {:.2f} C, relative humidity {:.2f}%".format(temperatures['celsius']['value'], humidity['relative']['value']))
    timestamps = Util.TimeStamp.timestamps()
    return {
        "timestamp": timestamps['iso8601'],
        "timestamp_epoch": timestamps['epoch'],
        "temperature": temperatures, 
        "humidity": humidity
    }

def write_file(data):
    logger.debug(f'writing : {HISTORY_FILE}')
    Util.File.write(data, HISTORY_FILE)

def read_file():
    if os.path.exists(HISTORY_FILE):
        logger.debug(f'reading : {HISTORY_FILE}')
        return Util.File.read(HISTORY_FILE)
    logger.info(f'no input file, creating base object')
    return create_base_object()

def create_base_object():
    timestamps = Util.TimeStamp.timestamps()
    return {
        "data" : [],
        "count": 0,
        "interval": SLEEP_DURATION,
        "updated": {
            "timestamp": timestamps['iso8601'],
            "timestamp_epoch": timestamps['epoch'],
        }
    }

def signal_handler(_signo, _stack_frame):
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# reset the input file if requested
if len(sys.argv) > 1:
    if sys.argv[1] == 'reset':
        logger.info(f'file reset requested, writing base object')
        data = create_base_object()
        write_file(data)

# main loop, continue forever
while True:
    data = read_file()
    update_data = get_reading()
    data['data'].append(update_data)
    
    if(len(data['data']) > MAX_COUNT):
        del data['data'][0]

    data['count'] = len(data['data'])
    timestamps = Util.TimeStamp.timestamps()
    data['updated']['timestamp'] = timestamps['iso8601']
    data['updated']['timestamp_epoch'] = timestamps['epoch']

    write_file(data)
    sleep(SLEEP_DURATION)
