# api
The code for the Flask Api for serving internal data to the frontend application

## Requirements
This api is for serving data from a raspberry pi computer with an attached [HTU21D](https://learn.sparkfun.com/tutorials/htu21d-humidity-sensor-hookup-guide) temperature and humidity sensor installed.  This code will not function properly unless you have those two things and they are working (I2C is set up and you can read the sensor data).  As an additional requirement the garage door code requires having HT0740 relays connected to something that will control the garage door via shorting a switch.

### Expected Environment Variables
```shell
API_ACCESS_TOKEN= #the token to use to allow access to the garage control method
API_ADMIN_USER= #the username to allow setting the access token on the client machine via the login
API_ADMIN_PASS= #the password to allow setting the access token on the client machine via the login

optional

API_HISTORY_MAX= #how many history points to maintain in the history file (default 1440)
API_HISTORY_DURATION= #the duration between read events to update the history file (seconds, defaults to 60)
```

## Endpoints
This describes the endpoints that are exposed via this api

### GET /sensor/
The sensor data is returned separate from the CPU temperature data so they are able to be polled at different intervals.  This is from the [HTU21D](https://learn.sparkfun.com/tutorials/htu21d-humidity-sensor-hookup-guide) temperature and humidity sensor from [Sparkfun](https://www.sparkfun.com/).  I will be trying to get some time to evaluate the [Eviro hat](https://shop.pimoroni.com/products/enviro?variant=31155658489939) from [Pimoroni](https://shop.pimoroni.com/), but from what I have seem of the inconsistent temperature readings I have no plans to replace the HTU21D sensor in the immediate future.  The response format is in json in the following

```json
{
    "temperature": {
        "celsius": { "value": number, "symbol": "°C" },
        "fahrenheit": { "value": number, "symbol": "°F" },
        "kelvin": { "value": number, "symbol": "K" },
        "rankine": { "value": number, "symbol": "°R" }
    },
    "humidity": {
        "relative": { "value": number, "symbol": "RH" },
        "absolute": { "value": number, "symbol": "mg/m³" }
    }
}
```

### GET /system/
The CPU temperature and system level information is contained in this endpoint.  This is somewhat of a work in progress endpoint and can be expected to change with new major versions released as more data is made available over it.  Hopefully it will be simply added to and existing data should not need to be reformatted.

```json
{
    "cpu":{
        "temperature": {
            "celsius": { "value": number, "symbol": "°C" },
            "fahrenheit": { "value": number, "symbol": "°F" },
            "kelvin": { "value": number, "symbol": "K" },
            "rankine": { "value": number, "symbol": "°R" }
        }
    },
    "uptime":{
        "epoch": integer,
        "days": integer,
        "hours": integer,
        "seconds": integer
    },
    "partitons": {
        <mount>: {
            "mount": string,
            "device": string,
            "fstype": string,
            "usages":{
                "free_space": integer,
                "used_space": integer,
                "total_space": integer,
                "percent_used": number
            }
        }
    }
}
```