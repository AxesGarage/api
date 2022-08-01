from math import log10
import json
from sqlite3 import Timestamp
import htu21
from time import time
from math import floor

class Convert:
    '''Conversion functions'''

    @staticmethod
    def temperature(celsius):
        """Convert the celsius passed temperature to all 4 major scales"""
        fahrenheit = ((9.0 / 5.0) * celsius) + 32
        rankine = fahrenheit + 459.67
        kelvin = celsius + 273.15
        return {
            'celsius': celsius,
            'fahrenheit': fahrenheit,
            'rankine': rankine,
            'kelvin': kelvin,
        }

    @staticmethod
    def calculateDewPoint(celsius, rh):
        """calculate the Dew Point from the current temperature and relative humidity"""
        a = 8.1332
        b = 1762.39
        c = 235.66
        pp_t = pow(10, (a - (b / (celsius + c))))
        t_d = - ((b / (log10(rh * (pp_t / 100)) - a)) + c)
        return {'dewPoint': Format.Temperatures(Convert.convertTemperature(t_d))}

class Format:

    @staticmethod
    def temperatures(temps):
        """format the temperature array returned in temperature() with additional information"""
        return {
            'celsius': {'value': temps['celsius'], 'symbol': '°C'},
            'fahrenheit': {'value': temps['fahrenheit'], 'symbol': '°F'},
            'rankine': {'value': temps['rankine'], 'symbol': '°R'},
            'kelvin': {'value': temps['kelvin'], 'symbol': 'K'}
        }

    @staticmethod
    def humidity(celsius, rh):
        humidity = {'relative': {'value': rh, 'symbol': '%RH'}}
        humidity.update(Convert.calculateDewPoint(celsius, rh))
        return humidity

    @staticmethod
    def float(float_val):
        return round(float_val, 2)

class File:
    @staticmethod
    def read(filename):
        with open(filename, "r") as read_file:
            return json.load(read_file)

    @staticmethod
    def write(data, filename):
        with open(filename, "w") as write_file:
            json.dump(data, write_file)


class Htu21:
    @staticmethod
    def read():
        """Read the HTU21's temperature and humidity sensor values"""
        htu = htu21.HTU21()
        return {'temp_c': htu.read_temperature(), 'humidity_relative': htu.read_humidity()}

class TimeStamp:
    @staticmethod
    def epoch(time):
        return floor(time.time())
    
    def isoFormat(date_time):
        return date_time.isoFormat()
    
    def timestamps(date_time):
        return {
            'iso8601': TimeStamp.isoFormat(date_time),
            'epoch': Timestamp.epoch(time(date_time))
        }