from flask import Flask, request, make_response, redirect
from flask_restful import Api, Resource
from os import statvfs
from uptime import boottime
from datetime import datetime
from collections import namedtuple
from time import sleep
import os
from ht0740 import HT0740
from axe.util import Convert, Format, Htu21

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
        clamp = lambda n, minn, maxn: max(min(maxn, n), minn)
        data = Htu21.read()
        temperatures = Convert.temperature(data['temp_c'])
        humidity = Format.humidity(data['temp_c'], clamp(data['humidity_relative'], 0, 100))
        return {"temperature": Format.temperatures(temperatures), "humidity": humidity}

class System(Resource):
    @staticmethod
    def get():
        cpu_temps = Convert.temperature(get_cpu_temperature())
        partitions = dict()
        for part in disk_partitions():
            partitions[part.mountpoint] = getFsStats(part.mountpoint)
            partitions[part.mountpoint]['device'] = part.device
            partitions[part.mountpoint]['fstype'] = part.fstype

        # remove the 0 total and used space items from the paritions, nothing interesting to report there, just noise
        partitions = dict(filter(lambda x: x[1]['usage']['total_space'] > 0, partitions.items()))
        partitions = dict(filter(lambda x: x[1]['usage']['used_space'] > 0, partitions.items()))
        return {
            "cpu": {"temperature": Format.temperatures(cpu_temps)},
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
