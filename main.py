# coding=utf-8
# Copyright (c) 2013-2016 Intel, Inc.
# Author Igor Stoppa <igor.stoppa@intel.com>
# Author Topi Kuutela <topi.kuutela@intel.com>
# Author Erkka Kääriä <erkka.kaaria@intel.com>
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
Main entry point for aft.
"""

import sys
import os.path
import argparse
import logging

import aft.config as config
import aft.tools.device_configuration_checker as device_config
from aft.logger import Logger as logger
import aft.devices.common as common
from aft.tools.thread_handler import Thread_handler as thread_handler
from aft.tools.topology_builder import TopologyBuilder
from aft.tools.edison_recovery_flasher import recover_edisons
from aft.devicesmanager import DevicesManager
from aft.tester import Tester


def main(argv=None):
    """
    Entry point for library-like use.
    """

    try:
        logger.init_root_logger()
        logger.init_process()

        config.parse()

        if argv != None:
            backup_argv = sys.argv
            sys.argv = argv

        args = parse_args()

        if args.debug:
            logger.level(logging.DEBUG)

        if args.configure:
            builder = TopologyBuilder(args)
            builder.build_topology()
            return 0

        if args.check:
            results = device_config.check(args)
            logger.info(results[1])
            print(results[1])

            if results[0] == True:
                return 0
            else:
                return 1
        elif args.checkall:
            results = device_config.check_all(args)
            logger.info(results[1])
            print(results[1])

            if results[0] == True:
                logger.info("All tests passed")
                return 0
            else:
                logger.info("There were failures")
                return 1


        device_manager = DevicesManager(args)

        if args.blacklist:
            if not args.device:
                print("Device must be specified for blacklisting")
                return 1

            device_manager.blacklist_device(args.device, args.reason)
            return 0

        if args.unblacklist:
            if not args.device:
                print("Device must be specified for unblacklisting")
                return 1
            device_manager.unblacklist_device(args.device)
            return 0

        if args.blacklist_print:
            device_manager.blacklist_print()
            return 0

        if args.recover_edisons:
            recover_edisons(device_manager, args.verbose)
            return 0

        if not args.model:
            print("Both model and image must be specified")
            return 1

        if not args.noflash:
            if not args.file_name:
                print("Both model and image must be specified")
                return 1

            if not os.path.isfile(args.file_name):
                print("Didn't find image: " + args.file_name)
                logger.error("Didn't find image: " + args.file_name)
                return 1

        if args.device:
            device, tester = try_flash_specific(args, device_manager)
        else:
            device, tester = try_flash_model(args, device_manager)

        if not args.notest:
            print("Testing " + str(device.name) + ".")
            tester.execute()

        if not args.nopoweroff:
            device.detach()

        device_manager.release(device)

        if "backup_argv" in locals():
            sys.argv = backup_argv
        return 0

    except KeyboardInterrupt:
        print("Keyboard interrupt, stopping aft")
        logger.error("Keyboard interrupt, stopping aft.")
        sys.exit(0)

    except:
        _err = sys.exc_info()
        logger.error(str(_err[0]).split("'")[1] + ": " + str(_err[1]))
        raise

    finally:
        thread_handler.set_flag(thread_handler.RECORDERS_STOP)
        for thread in thread_handler.get_threads():
            thread.join(5)

def try_flash_specific(args, device_manager):
    '''
    Reserve and flash specific device.

    Args:
        args: AFT arguments
        device_manager: Device manager object

    Returns:
        device, tester: Reserved device and tester handles.
    '''
    device = device_manager.reserve_specific(args.device, model=args.model)
    tester = Tester(device)

    if args.record:
        device.record_serial()

    if not args.noflash:
        print("Flashing " + str(device.name) + ".")
        device.write_image(args.file_name)
        print("Flashing successful.")

    return device, tester

def try_flash_model(args, device_manager):
    '''
    Reserve and flash a device. By default it tries to flash 2 times with 2
    different devices. If flashing fails 2 times the device will be blacklisted.

    Args:
        args: AFT arguments
        device_manager: Device manager object

    Returns:
        device, tester: Reserved device and tester handles.
    '''
    device_attempt = 0
    device_retries = args.device_retries

    while device_attempt < device_retries:
        device_attempt += 1

        device = device_manager.reserve()
        tester = Tester(device)

        if args.record:
            device.record_serial()

        if args.noflash:
            return device, tester

        flash_attempt = 0
        flash_retries = args.flash_retries

        while flash_attempt < flash_retries:
            flash_attempt += 1

            try:
                print("Flashing " + str(device.name) + ", attempt " +
                    str(flash_attempt) + " of " + str(flash_retries) + ".")
                device.write_image(args.file_name)
                print("Flashing successful.")
                return device, tester

            except KeyboardInterrupt:
                raise

            except:
                _err = sys.exc_info()
                _err = str(_err[0]).split("'")[1] + ": " + str(_err[1])
                logger.error(_err)
                print(_err)

                if (flash_retries - flash_attempt) == 0:
                    msg = "Flashing failed " + str(flash_attempt) + " times"
                    print(msg + ", blacklisting " + str(device.name))
                    logger.info(msg + ", blacklisting " + str(device.name))
                    common.blacklist_device(device.dev_id, device.name, msg)
                    device_manager.release(device)

                    if device_attempt < device_retries:
                        print("Trying to flash another device")

                    else:
                        raise

                elif (flash_retries - flash_attempt) == 1:
                    print("Flashing failed, trying again one more time")

                elif (flash_retries - flash_attempt) > 1:
                    print("Flashing failed, trying again " +
                        str(flash_retries - flash_attempt) + " more times")

def parse_args():
    """
    Argument parsing
    """
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--catalog",
        action="store",
        help="Configuration file describing the supported device types",
        default="/etc/aft/devices/catalog.cfg")

    parser.add_argument(
        "--topology",
        action="store",
        help="Configuration file describing the (physically) attached devices",
        default="/etc/aft/devices/topology.cfg")

    parser.add_argument(
        "model",
        action="store",
        nargs="?",
        help="Model type")

    parser.add_argument(
        "file_name",
        action="store",
        nargs="?",
        help = "Image to write: a local file, compatible with the selected " +
        "model."
        )

    parser.add_argument(
        "--device",
        type=str,
        nargs="?",
        action="store",
        default="",
        help="Specify the individual physical device by name.")

    parser.add_argument(
        "--device_retries",
        type=int,
        nargs="?",
        action="store",
        default="2",
        help="Specify how many devices will be tried if flashing fails.")

    parser.add_argument(
        "--flash_retries",
        type=int,
        nargs="?",
        action="store",
        default="2",
        help="Specify how many times flashing will be tried on one device .")

    parser.add_argument(
        "--record",
        action="store_true",
        default=False,
        help="Record the serial output during testing to a file " +
            "from the serial_port and serial_bauds defined in configuration.")

    parser.add_argument(
        "--noflash",
        action="store_true",
        default=False,
        help="Skip device flashing")

    parser.add_argument(
        "--notest",
        action="store_true",
        default=False,
        help="Skip test case execution (still creates a test plan)")

    parser.add_argument(
        "--nopoweroff",
        action="store_true",
        default=False,
        help="Do not power off the DUT after testing")

    parser.add_argument(
        "--check",
        action="store_true",
        help="Check that device is configured correctly")

    parser.add_argument(
        "--checkall",
        type=str,
        nargs="?",
        const="fast",
        action="store",
        choices=["fast", "accurate"],
        help="Check configurations for all devices. Defaults to fast")

    parser.add_argument(
        "--configure",
        type=str,
        nargs="?",
        const="dryrun",
        action="store",
        choices=["dryrun", "save"],
        help=("Find and configure devices. Dryrun merely prints the configs, "
            "save actually saves them. Defaults to dryrun"))

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Prints additional information on various operations")

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Increases logging level")

    parser.add_argument(
        "--blacklist",
        action="store_true",
        help=("Blacklist a device. The device must be specified with --device. "
            "--reason can be used to provide a reason"))

    parser.add_argument(
        "--unblacklist",
        action="store_true",
        help=("Removes device from the blacklist. The device must be specified"
            "with --device."))

    parser.add_argument(
        "--reason",
        action="store",
        help="Reason for given operation",
        default="No reason given")

    parser.add_argument(
        "--blacklist_print",
        action="store_true",
        help="Print the contents of the blacklist")

    parser.add_argument(
        "--recover_edisons",
        action="store_true",
        help="Lock all Edisons and recover blacklisted ones")

    return parser.parse_args()

if __name__ == "__main__":
    sys.exit(main())
