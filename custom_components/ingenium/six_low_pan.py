import datetime
import json
import time
from collections import deque
from threading import Thread
from typing import Optional, Dict

from ingeniumpy import IngeniumAPI
from ingeniumpy.objects import IngSif, IngAirSensor, IngComponent, IngMeterBus, IngActuator, \
    IngBusingRegulator
from serial import Serial

DOMAIN = "ingenium"

SIXLOWPAN_ENABLED = False
DEBUG = True
SERIAL_PORT = "/dev/ttyS6LP"


class SixLowPan:
    """
    Main 6LowPan communication class, to load it automatically, make sure
    there is an import for it in custom_components/ingenium/__init__.py like this:

      from ingeniumpy import IngeniumAPI
      from .six_low_pan import SixLowPan

    It's important that it goes _after_ the IngeniumAPI import.

    Also make sure that custom_components/ingenium/manifest.json contains the pyserial dependency:

      "requirements": [
        "ingeniumpy==0.7.2",
        "pyserial==3.5"
      ],

    Note: While Home Assistant supports adding multiple instances for each integration, e.g.
    multiple independent Ingenium installlations, this is not supported by this 6LowPan module,
    which needs to communicate throught an exclusive serial connection
    """

    api: IngeniumAPI
    read_thread: Thread
    write_thread: Thread
    write_queue: deque = deque(maxlen=256)
    serial: Optional[Serial] = None
    last_updates: Dict[str, datetime.datetime] = {}

    def init(self, api: IngeniumAPI):
        """
        This gets called when the Ingenium API communication gets started, and
        it adds notification listeners for all the devices it supports
        """
        self.api = api

        for o, c, i in api.get_sifs():
            c.add_update_notify(lambda _o=o, _c=c, _i=i: self.update_multisensor(_o, _c, _i))
        for o, c, i in api.get_meterbuses():
            c.add_update_notify(lambda _o=o, _c=c, _i=i: self.update_meterbus(_o, _c, _i))
        for o, c, i in api.get_air_sensors():
            c.add_update_notify(lambda _o=o, _c=c, _i=i: self.update_air_sensor(_o, _c, _i))
        for o, c in api.get_switches():
            c.add_update_notify(lambda _o=o, _c=c: self.update_actuator(_o, _c))
        for o, c in api.get_lights():
            c.add_update_notify(lambda _o=o, _c=c: self.update_dimmer(_o, _c))

        # Threads for reading and writing to the 6LowPan network
        self.read_thread = Thread(target=self.read_thread_loop)
        self.write_thread = Thread(target=self.write_thread_loop)
        self.read_thread.start()
        self.write_thread.start()

    #####################################################################################################
    # Here are the funcions called when a device is updated, separated by type.                         #
    # Modify this to change what is sent to the network.                                                #
    #####################################################################################################

    def update_multisensor(self, obj: IngSif, comp: IngComponent, mode: int):
        """
        Modes represent temperature, pressence, illuminance and humidity.
        Units are ºC, boolean value, lux, and %
        """
        modes_names = ["T", None, "P", "L", "H"]
        identifier = DOMAIN + "." + comp.id + "_" + modes_names[mode]  # Internal ID in HA
        name = comp.label + " " + modes_names[mode]  # Name as shown in HA
        value = obj.get_value(mode)  # Value

        j = json.dumps({"type": "MUL", "id": identifier, "name": name, "value": value})
        self.write_string(j)

    def update_meterbus(self, obj: IngMeterBus, comp: IngComponent, channel: int):
        identifier = DOMAIN + "." + comp.id + "_C" + str(channel)  # Internal ID in HA
        name = comp.label + " C" + str(channel)  # Name as shown in HA
        value = obj.get_cons(channel)  # Value in Watts

        j = json.dumps({"type": "MET", "id": identifier, "name": name, "value": value})
        self.write_string(j)

    def update_air_sensor(self, obj: IngAirSensor, comp: IngComponent, mode: int):
        """Measurement is 0 for CO2, and 1 for VOCs"""
        measurements = ["CO2", "VOCs"]

        identifier = DOMAIN + "." + comp.id + "_" + measurements[mode].lower()  # Internal ID in HA
        name = comp.label + " " + measurements[mode]  # Name as shown in HA
        value = obj.get_value(mode)  # Value

        j = json.dumps({"type": "AIR", "id": identifier, "name": name, "value": value})
        self.write_string(j)

    def update_actuator(self, obj: IngActuator, comp: IngComponent):
        identifier = DOMAIN + "." + comp.id  # Internal ID in HA
        name = comp.label  # Name as shown in HA
        is_on = obj.get_switch_val(comp)  # True/False

        consumption = obj.consumption  # This is -1 when the device doesn't measure power, and >= 0 when it does
        current = obj.current
        voltage = obj.voltage
        active_power = obj.active_power

        j = json.dumps({"type": "ACT", "id": identifier, "name": name, "value": is_on, "consumption": consumption,
                        "voltage": voltage, "current": current, "active_power": active_power})
        self.write_string(j)

    def update_dimmer(self, obj: IngBusingRegulator, comp: IngComponent):
        identifier = DOMAIN + "." + comp.id  # Internal ID in HA
        name = comp.label  # Name as shown in HA
        value = obj.get_value(comp.output)  # 0-100

        j = json.dumps({"type": "DIM", "id": identifier, "name": name, "value": value})
        self.write_string(j)

    #####################################################################################################
    # End of device update functions.                                                                   #
    #####################################################################################################

    def write_string(self, data: str):
        if DEBUG:
            print("SEND {}".format(data))
        self.write_queue.append((data + "\r\n").encode())

    def read_thread_loop(self):
        line_bytes = bytearray()
        while True:
            try:
                if self.serial is None or not self.serial.is_open:
                    self.serial = Serial(port=SERIAL_PORT, baudrate=115200, timeout=None)
                    time.sleep(1)

                print("# Serial Open #")

                open_errors = 0
                while True:
                    if not self.serial or not self.serial.is_open:
                        print("Serial not open, retry")
                        time.sleep(2)
                        open_errors += 1

                        if open_errors == 5:
                            break
                        continue

                    read = self.serial.read(size=1)
                    if read is None:
                        print("Serial read None")
                        break

                    line_bytes.extend(read)

                    if read == b"\n" or read == b"\r":
                        line = line_bytes.decode()
                        line_bytes = bytearray()
                        if DEBUG:
                            print("READ {}".format(line))

                print("Serial is closed, reopening")

            except BaseException as e:
                print("Exception in serial read thread: ", e)

    def write_thread_loop(self):
        while True:
            try:
                if self.serial is None or not self.serial.is_open:
                    time.sleep(1)

                if len(self.write_queue) == 0:
                    time.sleep(0.1)
                    continue

                item = self.write_queue.popleft()
                self.serial.write(item)

            except BaseException as e:
                print("Exception in serial write thread: ", e)


# Run this when this file gets loaded when imported
if SIXLOWPAN_ENABLED:
    IngeniumAPI.onload = lambda api: SixLowPan().init(api)

