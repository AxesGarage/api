from flask import Flask, request, make_response, redirect
from flask_restful import Api, Resource
from math import log10
from os import statvfs
from uptime import boottime
from datetime import datetime
from collections import namedtuple
from time import sleep
import os
import htu21
from ht0740 import HT0740

disk_named_tuple = namedtuple('partition', 'device mountpoint fstype')

ACCESS_TOKEN = os.getenv('API_ACCESS_TOKEN')
ADMIN_USER = os.getenv('API_ADMIN_USER')
ADMIN_PASS = os.getenv('API_ADMIN_PASS')


def engage_garage_door(door_number):
    """Activate the garage door opener relay for the passed door"""
    res = False
    try:
        i2cAddress = 55 + int(door_number)
        switch = HT0740(i2cAddress)  # the correct address for the relay must be set when creating the object
        res = switch.enable
        switch.on()
        sleep(0.5)
        switch.off()
        res = switch.disable
    except:
        return res
    return res


def get_cpu_temperature():
    """Read the temperature of the CPU returned in degrees Celsius"""
    t_file = open('/sys/class/thermal/thermal_zone0/temp')
    temp = float(t_file.read())
    return temp / 1000


def read_htu21():
    """Read the HTU21's temperature and humdidty sensor values"""
    htu = htu21.HTU21()
    return {'temp_c': htu.read_temperature(), 'humidity_relative': htu.read_humidity()}


def formatFloat(float_val):
    return round(float_val, 2)


def convertTemperature(celsius):
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


def formatTemperatures(temps):
    """format the temperature array returned in convertTemperature() with additional information"""
    return {
        'celsius': {'value': temps['celsius'], 'symbol': '°C'},
        'fahrenheit': {'value': temps['fahrenheit'], 'symbol': '°F'},
        'rankine': {'value': temps['rankine'], 'symbol': '°R'},
        'kelvin': {'value': temps['kelvin'], 'symbol': 'K'}
    }


def calculateDewPoint(celsius, rh):
    """calculate the Dew Point from the current temperature and relative humidity"""
    a = 8.1332
    b = 1762.39
    c = 235.66
    rh = min(rh, 100)  # rh of over 100 is just a biproduct of the sensor, over 100 is not physically possible
    if rh >= 100:
        return {'dewPoint': formatTemperatures(convertTemperature(celsius))}
    pp_t = pow(10, (a - (b / (celsius + c))))
    t_d = - ((b / (log10(rh * (pp_t / 100)) - a)) + c)
    return {'dewPoint': formatTemperatures(convertTemperature(t_d))}


def formatHumidity(celsius, rh):
    humidity = {'relative': {'value': rh, 'symbol': '%RH'}}
    humidity.update(calculateDewPoint(celsius, rh))
    return humidity


def disk_partitions(virtual=False):
    """Return all mounted partitions as a nametudple.
    If all == False return physical partitions only.
    """
    phydevs = []
    f = open("/proc/filesystems", "r")
    for line in f:
        if not line.startswith("nodev"):
            phydevs.append(line.strip())

    retlist = []
    f = open('/etc/mtab', "r")
    for line in f:
        if not virtual and line.startswith('none'):
            continue
        fields = line.split()
        device = fields[0]
        mountpoint = fields[1]
        fstype = fields[2]
        if not all and fstype not in phydevs:
            continue
        if device == 'none':
            device = ''
        named_tuple = disk_named_tuple(device, mountpoint, fstype)
        retlist.append(named_tuple)
    return retlist


def getFsStats(path):
    """Return the disk usage of the path passed """
    st = statvfs(path)
    free = (st.f_bavail * st.f_frsize)
    total = (st.f_blocks * st.f_frsize)
    used = (st.f_blocks - st.f_bfree) * st.f_frsize
    try:
        percent = (float(used) / total) * 100
    except ZeroDivisionError:
        percent = 0
    # NB: the percentage is -5% than what shown by df due to
    # reserved blocks that we are currently not considering:
    # http://goo.gl/sWGbH
    return {
        'mount': path,
        'usage': {
            'free_space': free,
            'used_space': used,
            'total_space': total,
            'percent_used': percent
        }
    }


def generateUptime():
    """Generate the system uptime, with boot epoch and time since boot to now"""
    boot = boottime()
    elapsed = datetime.now() - boot
    elapsed_hours = elapsed.seconds // 3600
    elapsed_seconds = elapsed.seconds - (elapsed_hours * 3600)
    elapsed_minutes = elapsed_seconds // 60
    elapsed_seconds = elapsed_seconds - (elapsed_minutes * 60)
    return {
        "epoch": boot.timestamp(),
        "days": elapsed.days,
        "hours": elapsed_hours,
        "minutes": elapsed_minutes,
        "seconds": elapsed_seconds,
    }


class Sensor(Resource):
    @staticmethod
    def get():
        data = read_htu21()
        temperatures = convertTemperature(data['temp_c'])
        humidity = formatHumidity(data['temp_c'], data['humidity_relative'])
        return {"temperature": formatTemperatures(temperatures), "humidity": humidity}


class System(Resource):
    @staticmethod
    def get():
        cpu_temps = convertTemperature(get_cpu_temperature())
        partitions = dict()
        for part in disk_partitions():
            partitions[part.mountpoint] = getFsStats(part.mountpoint)
            partitions[part.mountpoint]['device'] = part.device
            partitions[part.mountpoint]['fstype'] = part.fstype

        # remove the 0 total and used space items from the paritions, nothing interesting to report there, just noise
        partitions = dict(filter(lambda x: x[1]['usage']['total_space'] > 0, partitions.items()))
        partitions = dict(filter(lambda x: x[1]['usage']['used_space'] > 0, partitions.items()))
        return {
            "cpu": {"temperature": formatTemperatures(cpu_temps)},
            "uptime": generateUptime(),
            "partitions": partitions
        }


class Garage(Resource):
    @staticmethod
    def get():
        garage_number = request.args.get("door")
        access = request.cookies.get('access')
        if ACCESS_TOKEN is not None and access == ACCESS_TOKEN:
            success = engage_garage_door(garage_number)
            return {
                "doorNumber": garage_number,
                "result": 'success' if success else 'failed'
            }
        else:
            return {
                "doorNumber": garage_number,
                "result": "unauthorized"
            }


class LogIn(Resource):
    @staticmethod
    def post():
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USER and password == ADMIN_PASS:
            response = make_response(redirect('/'))
            response.set_cookie('access', ACCESS_TOKEN)
            return response
        else:
            return {
                "result": "unauthorized"
            }


app = Flask(__name__)
api = Api(app)
api.add_resource(Sensor, "/sensor")
api.add_resource(System, "/system")
api.add_resource(Garage, "/garage")
api.add_resource(LogIn, "/logInRequest")


@app.after_request
def prepare_response(response):
    response.headers.set('Access-Control-Allow-Origin', '*')
    response.headers.set('Access-Control-Allow-Methods', 'GET, POST')
    return response
