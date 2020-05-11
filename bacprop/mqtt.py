import asyncio
import json
from typing import AsyncIterable, Dict, NoReturn, Union

import random
import base64

from bacpypes.debugging import ModuleLogger, bacpypes_debugging
# from hbmqtt.broker import Broker
from hbmqtt.client import QOS_2, MQTTClient

_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
class SensorStream(MQTTClient):
    # BROKER_CONFIG = {
    #     "listeners": {"default": {"type": "tcp", "bind": "0.0.0.0:1883"}},
    #     "topic-check": {"enabled": False},
    # }
	
    DATA_CONFIG = {
        "test1":"data1",
        "test2":"data2"
    }

    def __init__(self) -> None:
        # pylint: disable=no-member
        SensorStream._info("Initialising broker on 0.0.0.0:1883")
        # self._broker = Broker(SensorStream.BROKER_CONFIG, asyncio.get_event_loop())
        self._running = False
        MQTTClient.__init__(self)

    async def start(self) -> Union[None, NoReturn]:
        # if _debug:
        #     # pylint: disable=no-member
        #     SensorStream._debug("Starting broker")
        # await self._broker.start()

        if _debug:
            # pylint: disable=no-member
            SensorStream._debug("Connecting to broker")
        # await self.connect("mqtt://localhost")
        await self.connect("mqtt://192.168.1.113")

        if _debug:
            # pylint: disable=no-member
            SensorStream._debug("Subscribing to sensor stream")
        # await self.subscribe([("application/#/device/#/# ", QOS_2)])
        await self.subscribe([("application/#", QOS_2)])

        self._running = True
        return None

    async def stop(self) -> Union[None, NoReturn]:
        if _debug:
            # pylint: disable=no-member
            SensorStream._debug("Stopping")

        if not self._running:
            return None

        if _debug:
            # pylint: disable=no-member
            SensorStream._debug("Shutting down broker")

        await self.disconnect()
        # await self._broker.shutdown()

        self._running = False

        return None

    async def read(self) -> AsyncIterable[Dict[str, float]]:
        while self._running:
            msg = await self.deliver_message()
            packet = msg.publish_packet

            # Decode the JSON data
            try:
                data = json.loads(packet.payload.data)
                deviceName = data["deviceName"]
                random.seed(deviceName)
                result = data["data"]
                temp = int(base64.b64decode(result), 16)
                data["data"]  =  temp
                self.DATA_CONFIG[SENSOR_ID_KEY] = random.randint(0, 1000000)
                data.update(self.DATA_CONFIG)
                yield data
            except json.JSONDecodeError as e:
                # pylint: disable=no-member
                SensorStream._error(f"Could not decode sensor data: {e}")
