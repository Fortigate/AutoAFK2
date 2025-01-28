"""Emulator Client Module."""

import os
import scrcpy
import sys
from configparser import ConfigParser
from functools import partial
from logging import Logger
from ppadb.client import Client
from subprocess import Popen, PIPE
from typing import Any, Union  # TODO: Update Python. Union required for Python <3.10

from automation.utility import _wait


class EmulatorClient:
    """Emulator Client Class."""

    def __init__(self, config: ConfigParser, logger: Logger) -> None:
        """Initialize the emulator.

        Args:
            config (ConfigParser): Configurations from settings.ini.
            logger (Logger): Logger.
        """
        self.device: Union[Any, None] = None
        self.config: ConfigParser = config
        self.adb: Client = Client(host="127.0.0.1", port=5037)
        self.cwd: str = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.logger: Logger = logger

        self.wait = partial(
            _wait, multiplier=self.config.getfloat("ADVANCED", "loading_multiplier")
        )  # TODO: Overkill

    def manage_adb_exe(self, command: str, device_name: str = "127.0.0.1:5555") -> None:
        """Get the right ADB path depending on whether we run from Pycharm or compiled .exe.

        Args:
            command (str): String "start", "restart" or "connect".
            device_name (str, optional): Device name. Defaults to "127.0.0.1:5555".
        """
        if os.path.isfile((self.cwd + "\\output\\adb\\adb.exe")):
            adbpath = os.path.join(
                self.cwd, "output", "adb", "adb.exe"
            )  # Locate adb.exe in working directory
        else:
            adbpath = os.path.join(
                self.cwd, "adbutils", "binaries", "adb.exe"
            )  # Locate adb.exe in working directory

        if command == "start":
            Popen([adbpath, "start-server"], stderr=PIPE).communicate()[0]

        if command == "restart":
            Popen([adbpath, "kill-server"], stderr=PIPE).communicate()[0]
            Popen([adbpath, "start-server"], stderr=PIPE).communicate()[0]

        if command == "connect":
            # logger.info(Popen([adbpath, 'connect', device_name], stdout=PIPE).communicate()[0].decode())
            Popen([adbpath, "connect", device_name], stdout=PIPE).communicate()[0]

    def get_adb_device(self) -> Union[Any, None]:
        """Start ADB, find, and connect to the device.

        Returns:
            Any | None: Found devices.
        """
        try:
            self.adb.devices()
        except Exception:
            self.manage_adb_exe("start")

        # If adb.devices contains devices and we can have auto-connect enabled we use the first one returned
        if (
            self.adb.devices()
            and self.config.getboolean("ADVANCED", "auto_find_device") is True
        ):
            devices = self.adb.devices()
            return devices[0]
        # Else manually connect using port in settings.ini
        else:
            self.logger.info(
                "Connecting manually with port: " + self.config.get("ADVANCED", "port")
            )
            device_name = "127.0.0.1:" + self.config.get("ADVANCED", "port")
            self.manage_adb_exe("connect", device_name)
            for found_devices in self.adb.devices():
                if found_devices.serial[-4:] == self.config.get(
                    "ADVANCED", "port"
                ):  # If device's port matches setting's port return the device
                    return found_devices
            # Else report nothing found
            self.logger.info(
                "No device found with port " + self.config.get("ADVANCED", "port")
            )

    def connect(self) -> None:
        """Connect to the emulator."""
        counter: int = 0
        self.device = self.get_adb_device()  # Find and connect to the device

        # After getting device run a test echo command to make sure the device is active and catch any errors
        try:
            # If this command is succesul we're connected! (to something at least..)
            self.device.shell("test")
        except Exception as e:
            # Else print the error and description and close after 15 seconds
            self.logger.info("Connection error:")
            nonetype = "'NoneType' object has no attribute 'shell'"
            offline = "ERROR: 'FAIL' 000edevice offline"
            string = "'str' object has no attribute 'shell'"
            self.logger.info(e)
            if str(e) == nonetype:
                self.logger.info(
                    "This means there's no device at the port in settings.ini, check port number or manually run 'adb devices' to check"
                )
            if str(e) == offline:
                self.logger.info(
                    "Device found but offline in ADB, try restarting the emulator and connecting again"
                )
            if str(e) == string:
                self.logger.info(
                    "Device search returned a string instead of a device, this shouldn't happen"
                )
                self.manage_adb_exe("restart")
            self.wait(15)
            sys.exit(2)

        # Once we're connected initialise scrcpy
        try:
            scrcpy_client = scrcpy.Client(device=self.device.serial)
            scrcpy_client.max_fps = 5
            scrcpy_client.bitrate = 16000000
            scrcpy_client.start(daemon_threaded=True)
            setattr(self.device, "srccpy", scrcpy_client)
        except Exception as e:
            self.logger.info("Error starting scrcpy!: " + str(e))
        finally:
            self.logger.info(
                "Device " + str(self.device.serial) + " connected successfully"
            )

        # Automatic server selection if VN version is installed
        global_version = self.device.shell(
            "pm list packages com.farlightgames.igame.gp"
        )
        if str(global_version[-3:-1]) == "vn":
            self.logger.info("VN Client installed, setting server to VN")
            self.metadata.server = "vn"

        # Sometimes the game crashes when launching so we make sure its been running for 5 seconds before continuing
        self.device.shell("monkey -p " + self.metadata.server + " 1")
        self.wait(
            5
        )  # This long wait doesn't slow anything down as the game takes 60 seconds to load anyway
        while self.device.shell("pidof " + self.metadata.server) == "":
            counter += 1
            self.device.shell("monkey -p " + self.metadata.server + " 1")
            self.wait(
                5
            )  # This long wait doesn't slow anything down as the game takes 60 seconds to load anyway
            if counter > 5:
                self.logger.warning(
                    "Attempting to launch AFK Journey, but cannot detect AFK Journey running"
                )
