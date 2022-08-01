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

log_handler = TimedRotatingFileHandler("history", "midnight", 1)
log_handler.suffix = "%Y%m%d"
logger = logging.getLogger(__name__)
logger.addHandler(log_handler)

HISTORY_FILE = 'history.json'

def get_reading():
    data = Util.Htu21.read()
    temperatures = Util.Format.temperatures(Util.Convert.temperature(data['temp_c']))
    humidity = Util.Format.humidity(data['temp_c'], max(data['humidity_relative'], 100))
    logger.info('HTU21: read .... temp {temp_c:.2} C, relative humidity {humidity_relative:.2%}'.format(data))
    timestamps = Util.TimeStamp.timestamps(datetime.now())
    return {
        "timestamp": timestamps.iso8601,
        "timestamp_epoch": timestamps.epoch,
        "temperature": temperatures, 
        "humidity": humidity
    }

def write_file(data):
    logger.info(f'writing : {HISTORY_FILE}')
    Util.File.write(data, HISTORY_FILE)

def read_file():
    if os.path.exists(HISTORY_FILE):
        logger.info(f'reading : {HISTORY_FILE}')
        return Util.File.read(HISTORY_FILE)
    logger.info(f'no input file, creating base object')
    return create_base_object()

def create_base_object():
    timestamps = Util.TimeStamp.timestamps(datetime.now())
    return {
        "data" : {},
        "count": 0,
        "interval": SLEEP_DURATION,
        "updated": {
            "timestamp": timestamps.iso8601,
            "timestamp_epoch": timestamps.epoch,
        }
    }

def signal_handler(_signo, _stack_frame):
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# reset the input file if requested
if len(sys.argv > 1):
    if sys.argv[1] == 'reset':
        logger.info(f'file reset requested, writing base object')
        data = create_base_object()
        write_file(data)

# main loop, continue forever
while True:
    data = read_file()
    update_data = get_reading()
    data.data.push(update_data)
    
    if(len(data.data) > MAX_COUNT):
        data.data.pop()

    data.count = len(data.data)
    timestamps = Util.TimeStamp.timestamps(datetime.now())
    data.updated.timestamp = timestamps.iso8601
    data.updated.timestamp_epoch = timestamps.epoch

    write_file(data)
    sleep(SLEEP_DURATION)
