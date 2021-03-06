import asyncio
import json
from typing import AsyncIterable, Dict, NoReturn, Union

import random
import base64

import logging

from bacpypes.debugging import ModuleLogger, bacpypes_debugging
# from hbmqtt.broker import Broker
from hbmqtt.client import QOS_2, MQTTClient

from bacprop import config

_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
class SensorStream(MQTTClient):
    # BROKER_CONFIG = {
    #     "listeners": {"default": {"type": "tcp", "bind": "0.0.0.0:1883"}},
    #     "topic-check": {"enabled": False},
    # }


    def __init__(self) -> None:
        # pylint: disable=no-member
        # SensorStream._info("Initialising broker on 0.0.0.0:1883")
        # self._broker = Broker(SensorStream.BROKER_CONFIG, asyncio.get_event_loop())
        self._running = False
        MQTTClient.__init__(self)



        logging.getLogger("hbmqtt.client.plugins").setLevel(logging.INFO)
        # 限制了接受发送数据的debug日志 ,下面注释的这个 和上卖弄 这句话一个效果
        #self.plugins_manager.logger.setLevel(logging.INFO)


        logging.getLogger("hbmqtt.mqtt.protocol.handler").setLevel(logging.INFO)

    async def start(self) -> Union[None, NoReturn]:
        # if _debug:
        #     # pylint: disable=no-member
        #     SensorStream._debug("Starting broker")
        # await self._broker.start()

        if _debug:
            # pylint: disable=no-member
            SensorStream._debug("Connecting to broker")
        # await self.connect("mqtt://localhost")
        await self.connect(config.MQTT_SERVER_ADDRESS)

        if _debug:
            # pylint: disable=no-member
            SensorStream._debug("Subscribing to sensor stream")
        # await self.subscribe([("application/#/device/#/# ", QOS_2)])
        await self.subscribe([(config.MQTT_SUB_TOPIC, QOS_2)])

        self._running = True
        return None

    async def stop(self) -> Union[None, NoReturn]:
        if _debug:
            # pylint: disable=no-member
            SensorStream._debug("Stopping")

        if not self._running:
            return None

        # if _debug:
        #     # pylint: disable=no-member
        #     SensorStream._debug("Shutting down broker")

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

                yield data
            except json.JSONDecodeError as e:
                # pylint: disable=no-member
                SensorStream._error(f"Could not decode sensor data: {e}")
