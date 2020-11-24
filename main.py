from flask import Flask
from flask_restful import Api, Resource

app = Flask(__name__)
api = Api(app)

def formatFloat(floatVal):
    return round(floatVal, 2)

def convertTemperature(celsius):
    ''' celsius
    '''
    fahrenheit = ((9.0/5.0) * celsius) + 32
    rankine = fahrenheit + 484.87
    kelvin = celsius + 273.15
    return {
        'celsius': formatFloat(celsius),
        'fahrenheit': formatFloat(fahrenheit),
        'rankine': formatFloat(rankine),
        'kelvin': formatFloat(kelvin)
    }

class Sensor(Resource):
    def get(self):
        return {"temperature": convertTemperature(23.2), "humidity":{'relative':52.2, 'absolute': 34.5}}

api.add_resource(Sensor, "/sensor")

if __name__ == "__main__":
    app.run(debug=True)