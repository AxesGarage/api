from flask import Flask
from flask_restful import Api, Resource
import htu21
import os
from uptime import boottime
from datetime import datetime
from collections import namedtuple

disk_ntuple = namedtuple('partition',  'device mountpoint fstype')

def get_cpu_temperature():
    '''Read the temperateure of the CPU returned in degrees Celsius'''
    tFile = open('/sys/class/thermal/thermal_zone0/temp')
    temp = float(tFile.read())
    return temp/1000

def read_htu21():
    '''Read the HTU21's temperature and humdidty sensor values'''
    htu = htu21.HTU21()
    return {'temp_c': htu.read_temperature(), 'humidity_relative': htu.read_humidity()}

def formatFloat(floatVal):
    return round(floatVal, 2)

def convertTemperature(celsius):
    '''Convert the celsius passed temperature to all 4 major scales'''
    fahrenheit = ((9.0/5.0) * celsius) + 32
    rankine = fahrenheit + 459.67
    kelvin = celsius + 273.15
    return {
        'celsius': celsius,
        'fahrenheit':fahrenheit,
        'rankine':rankine,
        'kelvin': kelvin,
    }

def formatTemperatures(temps):
    '''format the tempertaure array returned in convertTemperature() with additional information'''
    return {
        'celsius': { 'value': temps['celsius'], 'symbol': '°C' },
        'fahrenheit': { 'value': temps['fahrenheit'], 'symbol': '°F' },
        'rankine': { 'value': temps['rankine'], 'symbol': '°R' },
        'kelvin': { 'value': temps['kelvin'], 'symbol': 'K' }
    } 

def formatHumidity(rh):
    return {'relative': {'value': rh, 'symbol': 'RH'}}

def disk_partitions(virtual=False):
    """Return all mountd partitions as a nameduple.
    If all == False return phyisical partitions only.
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
        ntuple = disk_ntuple(device, mountpoint, fstype)
        retlist.append(ntuple)
    return retlist

def getFsStats(path):
    '''Return the disk usage of the path passed '''
    st = os.statvfs(path)
    free = (st.f_bavail * st.f_frsize)
    total = (st.f_blocks * st.f_frsize)
    used = (st.f_blocks - st.f_bfree) * st.f_frsize
    try:
        percent = ret = (float(used) / total) * 100
    except ZeroDivisionError:
        percent = 0
    # NB: the percentage is -5% than what shown by df due to
    # reserved blocks that we are currently not considering:
    # http://goo.gl/sWGbH
    return {
        'mount':path,
        'usage':{
            'free_space': free,
            'used_space': used,
            'total_space': total,
            'percent_used': percent
        }
    }

def generateUptime():
    '''Generate the system uptime, with boot epoch and time since boot to now'''
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
    def get(self):
        data = read_htu21()
        temperatures = convertTemperature(data['temp_c'])
        
        return {"temperature": formatTemperatures(temperatures), "humidity": formatHumidity(data['humidity_relative'])}

class System(Resource):
    def get(self):
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
            "cpu": {"temperature": formatTemperatures(cpu_temps) },
            "uptime": generateUptime(),
            "partitions": partitions
        }

app = Flask(__name__)
api = Api(app)
api.add_resource(Sensor, "/sensor")
api.add_resource(System, "/system")

if __name__ == "__main__":
    app.run(host='0.0.0.0')
