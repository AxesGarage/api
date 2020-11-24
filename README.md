# api
The code for the Flask Api for serving internal data to the frontend application

## Requirements
This api is for serving data from a raspberry pi computer with an attached HTU21D temperature and humidity sensor installed.  This code will not function properly unless you have those two things and they are working (I2C is set up and you can read the sensor data).

## Endpoints
This describes the endpoints that are exposed via this api

### GET /sensor/
The sensor data is returned separate from the CPU temperature data so they are able to be polled at different intervals.  The response format is in json in the following

```json
{
    "temperature":{
        "celsius": float,
        "fahrenheit": float,
        "kelvin": float,
        "rankine": float
    },
    "humidity":{
        "relative": float,
        "absolute": float
    }
}
```

### GET /cpu/
The CPU temperature and system level information is contained in this endpoint.  This is somewhat of a work in progress endpoint and can be expected to change with new major versions released as more data is made available over it.