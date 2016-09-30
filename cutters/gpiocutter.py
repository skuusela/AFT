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

import os
from aft.cutter import Cutter

class GpioCutter(Cutter):
    """
    Class for handling Songle relay
    """

    def __init__(self, config):
        pass

    def connect(self):
        """
        Turns power on

        Returns:
            None
        """
        os.system("echo 1 > /sys/class/gpio/gpio60/value")

    def disconnect(self):
        """
        Turns power off

        Returns:
            None
        """
        os.system("echo 0 > /sys/class/gpio/gpio60/value")

    def get_cutter_config(self):
        """
        Returns cutter settings.
        """
        return 0
