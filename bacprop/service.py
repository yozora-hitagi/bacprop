import asyncio
import base64
import logging
import random
import time
import traceback
from threading import Thread
from typing import Dict, Any

from bacpypes.debugging import ModuleLogger, bacpypes_debugging
from hbmqtt.broker import Broker

from bacprop import config
from bacprop.bacnet.network import VirtualSensorNetwork
from bacprop.defs import Logable
from bacprop.mqtt import SensorStream

_debug = 1
_log = ModuleLogger(globals())


@bacpypes_debugging
class BacPropagator(Logable):
    # SENSOR_ID_KEY = "deviceName"
    SENSOR_OUTDATED_TIME = 60 * 10  # 10 Minutes

    def __init__(self) -> None:
        BacPropagator._info(f"Intialising SensorStream and Bacnet")
        self._stream = SensorStream()
        self._sensor_net = VirtualSensorNetwork(config.LISTEN)
        self._running = False

        # self._device_id_ = 0

    def _handle_sensor_data(self, data: Dict[str, Any]) -> None:

        if "deviceName" not in data:
            BacPropagator._warning(f"Drop for deviceName missing from sensor data: {data}")
            return

        random.seed(data["deviceName"])
        sensor_id = random.randint(0, 1000000)

        if "data" not in data:
            BacPropagator._warning(f"Drop for data missing from sensor data: {data}")
            return

        result = data["data"]
        strdata = base64.b64decode(result).hex()
        if len(strdata) < 14:
            BacPropagator._warning(f"Drop for data length error from sensor data: {data}")
            return
        temp = strdata[6:8] + strdata[4:6]
        data["temp"] = int(temp, 16) / 10
        data["humidity"] = int(strdata[12:14], 16) / 2
        del data["data"]

        # if BacPropagator.SENSOR_ID_KEY not in data:
        #     BacPropagator._warning(f"sensorId {BacPropagator.SENSOR_ID_KEY} missing from sensor data: {data}")
        #     return

        # try:
        #     sensor_id = int(data[BacPropagator.SENSOR_ID_KEY])
        # except ValueError:
        #     BacPropagator._warning(
        #         f"sensorId {data[BacPropagator.SENSOR_ID_KEY]} could not be decoded"
        #     )
        #     return
        #
        # if len(sensor_id) <= 0:
        #     BacPropagator._warning(
        #         f"sensorId {data[BacPropagator.SENSOR_ID_KEY]} is an invalid id"
        #     )
        #     return
        #
        # del data[BacPropagator.SENSOR_ID_KEY]

        BacPropagator._debug(f"rev {sensor_id} with data: {data}")

        # values: Dict[str, float] = {}
        #
        # # Only allow through data which are actually floats
        # for key in data:
        #     # if type(data[key]) not in (float, int):
        #     #     BacPropagator._warning(
        #     #         f"Recieved non-number value ({key}: '{data[key]}') from sensor id: {sensor_id}"
        #     #     )
        #     # else:
        #     #     values[key] = data[key]
        #     values[key] = data[key]

        sensor = self._sensor_net.get_sensor(sensor_id)

        if not sensor:
            sensor = self._sensor_net.create_sensor(sensor_id)

        sensor.set_values(config.SENSOR_DEFINE["temp"], data)

        if sensor.has_fault():
            if _debug:
                BacPropagator._debug(
                    f"Sensor {sensor_id} now has new data, so marking as OK"
                )
            sensor.mark_ok()

    async def _fault_check_loop(self) -> None:
        BacPropagator._info("Starting fault check loop")
        while self._running:
            for sensor_id, sensor in self._sensor_net.get_sensors().items():
                if (
                        not sensor.has_fault()
                        and abs(time.time() - sensor.get_update_time())
                        > BacPropagator.SENSOR_OUTDATED_TIME
                ):
                    if _debug:
                        BacPropagator._debug(
                            f"Sensor {sensor_id} data is outdated, notifying fault"
                        )
                    sensor.mark_fault()

            await asyncio.sleep(1)

    async def _main_loop(self) -> None:
        BacPropagator._info("Starting stream receive loop")
        await self._stream.start()

        async for data in self._stream.read():
            if _debug:
                BacPropagator._debug(f"Received: {data}")

            self._handle_sensor_data(data)

    def _start_bacnet_thread(self) -> Thread:
        BacPropagator._info("Starting bacnet sensor network")

        bacnet_thread = Thread(target=self._sensor_net.run)
        bacnet_thread.daemon = True
        bacnet_thread.start()

        return bacnet_thread

    def start(self) -> None:
        self._running = True

        bacnet_thread = self._start_bacnet_thread()

        asyncio.ensure_future(self._fault_check_loop())

        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self._main_loop())
        except KeyboardInterrupt:
            pass
        except:
            traceback.print_exc()

        self._running = False

        BacPropagator._info("Stopping stream loop")
        loop.run_until_complete(self._stream.stop())

        BacPropagator._info("Closing bacnet sensor network")
        self._sensor_net.stop()
        bacnet_thread.join()
