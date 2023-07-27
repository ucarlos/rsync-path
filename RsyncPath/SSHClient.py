#!/usr/bin/env python3
# -------------------------------------------------------------------------------
# Created by Ulysses Carlos on 07/15/2023 at 02:25 PM
#
# SSHClient.py
# A Simple SSH Client used to execute specific commands on a remote machine.
# -------------------------------------------------------------------------------

from fabric import Connection
# from invoke.runners import Result
from pathlib import Path, PureWindowsPath
from OSType import OSType
import logging


class SSHClient(object):
    """A simple SSH Client class to execute specific commands on a remote machine."""

    def __init__(self, username, hostname, port, os_type=OSType.UNKNOWN):
        """Construct the SSHClient Object."""
        self.ssh_connection = Connection(host=hostname, user=username, port=port)
        self.os_type = os_type
        self.shell_name = "/bin/bash" if self.os_type == OSType.POSIX else "cmd.exe"

    def check_directory_size_in_bytes(self, directory_path):
        """Retrieve the size of a specific directory on the remote machine."""
        logging.debug("SSHClient.check_directory_size(): Starting function...")
        if self.os_type == OSType.UNKNOWN:
            logging.debug("SSHClient.check_directory_size(): Cannot check the directory size on a Unknown OS.")
            return

        command = ""
        if self.os_type == OSType.POSIX:
            command = f"du -sb {str(directory_path)}"
        else:
            pass

        # Now run the damn thing:
        result = self.ssh_connection.run(command, shell=self.shell_name)

        return result.stdout

    def check_if_directory_exists(self, directory_path: Path):
        """Check if a directory exists on the remote machine."""
        logging.debug("SSHClient.check_if_directory_exists(): Starting function...")
        if self.os_type == OSType.UNKNOWN:
            logging.debug("SSHClient.check_directory_size(): Cannot check the directory size on a Unknown OS.")
            return

        command = ""
        if self.os_type == OSType.POSIX:
            command = f"test -d {str(directory_path)}"
        else:
            # Format the result for windows:
            windows_path = PureWindowsPath(directory_path)
            command = f"""
            @echo off
            IF exist {str(windows_path)} ( echo 0 )
            ELSE ( echo 1 )"
            """
            pass

        # Now return the result.
        # TODO: Retrieve the results somehow.
        result = self.ssh_connection.run(command, shell=self.shell_name)

        result_code = result.exited
        return result_code is not None and result_code == 0

    def create_root_remote_directory(self, directory_path):
        """Create the remote_root_main_directory if it does not exist."""
        logging.debug("SSHClient.create_root_remote_directory(): Starting function...")
        if self.os_type == OSType.UNKNOWN:
            logging.debug("SSHClient.check_directory_size(): Cannot check the directory size on a Unknown OS.")
            return

        command = ""
        if self.os_type == OSType.POSIX:
            command = f"mkdir -p {str(directory_path)}"
        else:
            pass

        # Now return the result.
        self.ssh_connection.run(command, shell=self.shell_name)
        return

