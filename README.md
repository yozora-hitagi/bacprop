# BACprop

A MQTT to BACnet relay. Translating IoT data into virtual sensors on a bacnet network.

## Usage

Running `bacprop` on a local network will allow IoT devices to send MQTT data representing sensor data to
`bacprop` where the sensor will be represented as a BACnet object on the same network.

The sensor must send a JSON MQTT message on the channel `sensor/<sensorId>`. The JSON object keys
will be translated to the properties of the BACnet Object, with the sensorId as the ID of the object.

A sensor message might look like:

```json
{
  "sensorId": 2,
  "temp": 5.3,
  "co2": 502
}
```

## Developing

`bacprop` is developed using `pipenv`

`pipenv install --dev` will install all requirements for development to take place.

`pipenv run python -m bacprop` can be used to test changes

`pipenv run test` will run all tests

## Running

`pipenv install` will install all requirements for running

`pipenv run python -m bacprop`

## Docker

Docker images have been provided for `bacprop`. Both an armv6 image and a x86 image exist.
