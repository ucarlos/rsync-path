#!/usr/bin/env python3
# -------------------------------------------------------------------------------
# Created by Ulysses Carlos on 07/26/2023 at 06:45 PM
#
# LocalClient.py
#
# -------------------------------------------------------------------------------

from OSType import OSType
from enum import Enum
from shlex import split
from subprocess import run, DEVNULL
from logging import debug, error, info


class LocalClient(object):
    """Simple class to run specific command line commands or functions on a local client."""

    def __init__(self, os_type: Enum = OSType.UNKNOWN):
        """Initialize the class."""
        self.os_type = os_type

    def ping(self, ip_address: str):
        """
        Verify that an connection to a remote machine can be made by sending a ping request.
        NOTE: A host may not respond to a ping request even if the ip address is valid.


        :param: ip_address
        :returns True if the remote address responds to the ping request. False otherwise.
        """
        info("LocalClient.ping(): Starting ping call:")
        if OSType.UNKNOWN:
            error("LocalClient.ping(): Cannot make a connection to an remote machine using an undefined OS Type.")
            return False

        argument = "-n" if OSType.WINDOWS else "-c"
        command = f"ping {argument} 1 {ip_address}"
        command_list = split(command)

        debug(f"LocalClient.ping(): Passing the following command list: {command_list}")
        return run(command_list, stdout=DEVNULL) == 0

    def get_local_directory_size(self, directory_path):
        """Determine the size of a directory in bytes."""
        debug(f"LocalClient.get_local_directory_size(): Getting the directory size of {str(directory_path)}")

        size_in_bytes = float(sum(file.stat().st_size for file in directory_path.glob('**/*') if file.is_file()))
        debug(f"LocalClient.get_local_directory_size(): Size of {str(directory_path)} is {size_in_bytes}")
        return size_in_bytes
