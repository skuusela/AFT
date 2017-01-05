# Copyright (c) 2017 Intel, Inc.
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

"""
Test case for testing basic things in Linux based OS
"""

import unittest
import aft.tools.ssh as ssh

class TestBaseOS(unittest.TestCase):
    '''
    Basic OS tests
    '''
    def test_check_dmesg_errors(self):
        output, return_code = ssh.dut_execute("dmesg")
        error_lines = ""
        for line in output:
            if "error" in line.lower():
                error_lines += line
        self.assertEqual(error_lines, "")

    def test_check_boot_errors(self):
        output, return_code = ssh.dut_execute("journalctl -ab")
        error_lines = ""
        for line in output:
            if "error" in line.lower():
                error_lines += line
        self.assertEqual(error_lines, "")
