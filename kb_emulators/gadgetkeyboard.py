# coding=utf-8
# Copyright (c) 2016 Intel, Inc.
# Author Simo Kuusela <simo.kuus@intel.com>
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; version 2 of the License
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.

"""
Base class for peripheral emulators like mice and keyboards.
"""

from aft.kb_emulators.kb_emulator import KeyboardEmulator
from gadget_kb_emulator.keyboard_emulator import KeyboardEmulator as Emulator

class GadgetKeyboard(KeyboardEmulator):
    """
    Gadget keyboard emulator class
    """
    _TIMEOUT = 5

    def __init__(self, config):
        super(GadgetKeyboard, self).__init__()
        self.kb_emulator = Emulator(emulator_path=config["emulator_path"])

    def send_keystrokes_from_file(self, _file, timeout=_TIMEOUT):
        """
        Method to send keystrokes from a file
        """
        self.kb_emulator.send_keystrokes_from_file(_file)
