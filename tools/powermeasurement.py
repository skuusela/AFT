# coding=utf-8
# Copyright (c) 2013-2016 Intel, Inc.
# Author Simo Kuusela <simo.kuusela@intel.com>
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; version 2 of the License
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.

from sys import stdout
import threading
import aft.tools.ssh as ssh
from aft.tools.thread_handler import Thread_handler as thread_handler

def measure_power():

    while True:
        try:
            power = ssh.remote_execute("192.168.30.63",
                                    ["sigrok-cli", "--driver=baylibre-acme",
                                    " --samples=1", "--channels=P1_ENRG_PWR",
                                    "--config", "samplerate=100"])

            power = power.split("\n")[1]
            power = power.split(" ")
            del power[0]
            power = "".join(power).strip("\n")
            stdout.write("\rPower usage: " + power)
            stdout.flush()
            if thread_handler.get_flag(thread_handler.RECORDERS_STOP):
                print("\n")
                return 0
        except:
            pass

def measurement_thread():
    measuring = threading.Thread(target=measure_power,args=(),name=("measuring"))
    measuring.start()
    thread_handler.add_thread(measuring)
