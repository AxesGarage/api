from flask import Flask
from flask_restful import Api, Resource
import htu21

app = Flask(__name__)
api = Api(app)

def read_htu21():
    htu = htu21.HTU21()
    return {'temp': htu.read_temperature(), 'humidity': htu.read_humidity()}

def formatFloat(floatVal):
    return round(floatVal, 2)

def convertTemperature(celsius):
    ''' celsius
    '''
    fahrenheit = ((9.0/5.0) * celsius) + 32
    rankine = fahrenheit + 459.67
    kelvin = celsius + 273.15
    return {
        'celsius': formatFloat(celsius),
        'fahrenheit': formatFloat(fahrenheit),
        'rankine': formatFloat(rankine),
        'kelvin': formatFloat(kelvin)
    }

class Sensor(Resource):
    def get(self):
        data = read_htu21()
        return {"temperature": convertTemperature(data['temp']), "humidity":{'relative':formatFloat(data['humidity'])}}

api.add_resource(Sensor, "/sensor")

if __name__ == "__main__":
    app.run(host='0.0.0.0')