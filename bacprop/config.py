MQTT_SERVER_ADDRESS = "mqtt://192.168.1.113"

MQTT_SUB_TOPIC = "application/#"

LISTEN = "0.0.0.0:47808"

DATA_CONFIG = {
    "test1": "data1",
    "test2": "data2"
}

from bacprop.bacnet.sensor import _CharacterStringValueObject, _AnalogValueObject

SENSOR_DEFINE = {
    "temp": {
        "deviceName": _CharacterStringValueObject,
        "temp": _AnalogValueObject,
        "humidity": _AnalogValueObject
    }
}
