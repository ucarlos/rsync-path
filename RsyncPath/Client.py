# -------------------------------------------------------------------------------
# Created by Ulysses Carlos on 07/15/2023 at 02:25 PM
#
# Client.py
# Simple SSH Client used to execute specific commands on a remote machine.
# -------------------------------------------------------------------------------

from fabric import Connection, Result
from invoke.exceptions import UnexpectedExit
from subprocess import run, DEVNULL
from pathlib import Path, PureWindowsPath
from shlex import split

from RsyncPath.OSType import OSType
from logging import debug, error

DEFAULT_SSH_PORT = 22


def can_connect_to_remote_machine(ip_address: str, remote_os_type: OSType):
    """Verify that a connection to a remote machine can be made by sending a ping request.
    NOTE: A host may not respond to a ping request even if the ip address is valid.

    :param: ip_address
    :returns True if the remote address responds to the ping request. False otherwise.
    """
    debug("Client.can_connect_to_remote_machine(): Starting ping call.")
    if ip_address is None or len(ip_address) == 0:
        error(f"Client.can_connect_to_remote_machine(): Cannot make a connection to {ip_address} using an "
              "username that is empty or None.")
        return False

    if remote_os_type != OSType.POSIX:
        error("Client.can_connect_to_remote_machine(): Cannot make a connection to an remote machine using an "
              "unsupported OS Type.")
        return False

    argument = "-n" if remote_os_type == OSType.WINDOWS else "-c"
    command = f"ping {argument} 1 {ip_address}"
    command_list = split(command)

    debug(f"Client.can_connect_to_remote_machine(): Passing the following command list: {command_list}")
    result = run(command_list, stdout=DEVNULL, stderr=DEVNULL)
    return result.returncode is not None and result.returncode == 0


def create_instance_from_available_hostnames(hostname_list: list[dict]):
    """Select an available client from a hostname list and return a Client instance."""
    debug("Client.create_client_instance_from_available_hostnames(): Searching for an available host.")
    index = 1
    for hostname_dict in hostname_list:
        hostname = hostname_dict.get("hostname", "")
        os_type = hostname_dict.get("os_type", "")
        username = hostname_dict.get("username", "")
        debug("Client.create_instance_from_available_hostnames(): "
              f"Checking if host {index} with username {username}, address {hostname} and os_type {os_type} is "
              f"available to connect:")
        if can_connect_to_remote_machine(hostname, os_type):
            return Client(username, hostname, DEFAULT_SSH_PORT, os_type)
        index += 1

    error_message = """Could not establish any connection to any remote machine on the IP List. Please
     check your internet connection and make sure that at least one of the remote machines is available."""
    raise RuntimeError(error_message)


def create_instance_from_username_and_available_hostnames(username: str, hostname_list: list[dict]):
    """Select an available client from a specified username and hostname list and return a Client instance."""
    debug("Client.create_client_instance_from_username_and_available_hostnames(): Searching for an available host.")

    if username is None or len(username) == 0:
        raise RuntimeError("Error: Cannot establish any connection to a machine on the IP List due to having a "
                           "username is that is either empty or None.")

    index = 1
    for hostname_dict in hostname_list:
        hostname = hostname_dict.get("hostname", "")
        os_type = hostname_dict.get("os_type", "")
        debug("Client.create_instance_from_username_and_available_hostnames(): "
              f"Checking if host {index} with username {username}, address {hostname} and os_type {os_type} is "
              f"available to connect:")
        if can_connect_to_remote_machine(hostname, os_type):
            return Client(username, hostname, DEFAULT_SSH_PORT, os_type)
        index += 1

    error_message = """Could not establish any connection to any remote machine on the IP List. Please check your
    internet connection and make sure that at least one of the remote machines is available."""
    raise RuntimeError(error_message)


class Client(object):
    """A simple Client class to execute specific commands on both your local and remote machines."""

    def __init__(self, username, hostname, port=DEFAULT_SSH_PORT, remote_os_type=OSType.UNKNOWN):
        """Construct the Client Object."""
        self.ssh_connection = Connection(host=hostname, user=username, port=port)

        self.username = username
        self.hostname = hostname
        self.port = port
        # Not used currently, but
        self.local_os_type = OSType.get_os_type()
        self.remote_os_type = remote_os_type
        self.remote_shell_name = "/bin/bash" if self.remote_os_type == OSType.POSIX else "cmd.exe"
        self.local_shell_name = "/bin/bash" if self.local_os_type == OSType.POSIX else "cmd.exe"

    def change_connection(self, username, hostname, port, os_type=None):
        """Close the current SSH connection and create a new one using the passed username, hostname and port
        variables.
        """
        if self.ssh_connection.is_connected():
            self.ssh_connection.close()
        self.ssh_connection = Connection(user=username, host=hostname, port=port)
        self.username = username
        self.hostname = hostname
        self.port = port
        if os_type is not None:
            self.remote_os_type = os_type

    def get_remote_directory_size_in_bytes(self, directory_path):
        """Retrieve the size of a specific directory on the remote machine."""
        debug("Client.get_remote_directory_size_in_bytes(): Starting function...")

        if self.remote_os_type != OSType.POSIX:
            debug("Client.get_remote_directory_size_in_bytes(): Cannot check the directory size on a unsupported "
                  "OS.")
            return

        command = ""
        if self.remote_os_type == OSType.POSIX:
            command = f"du -sLb \"{str(directory_path)}\""
        else:
            pass

        # Now run the damn thing:
        try:
            result: Result = self.ssh_connection.run(command, shell=self.remote_shell_name, hide=True)
        except UnexpectedExit as exception:
            exception_argument_list = exception.__str__().split("\n\n")
            invalid_command = exception_argument_list[1].split(":")[1]
            error_code = exception_argument_list[2].split(":")[1]

            debug(f"Client.get_remote_directory_size_in_bytes(): Received Unexpected Exit Code {error_code} when "
                  f"executing {invalid_command}. Returning None as the byte size.")
            return None

        # TODO: Handle SSH Exceptions gracefully (Test this by running sudo shutdown "+3" on the remote machine)

        # Now split the value:
        size_in_bytes = result.stdout.split("\t")[0] if self.remote_os_type == OSType.POSIX else result.stdout
        debug(f"Client.get_remote_directory_size_in_bytes(): Retrieved Exit Code {result.exited}; "
              f"Size of {str(directory_path)} is {size_in_bytes} byte(s)")
        return int(size_in_bytes)

    def get_local_directory_size_in_bytes(self, directory_path: Path):
        """Determine the size of a directory in bytes."""
        debug(f"Client.get_local_directory_size_in_bytes(): Getting the directory size of {str(directory_path)}")

        size_in_bytes = int(sum(file.stat().st_size for file in directory_path.glob('**/*') if file.is_file()))
        debug(f"Client.get_local_directory_size_in_bytes(): Size of {str(directory_path)} is {size_in_bytes}")
        return int(size_in_bytes)

    def does_remote_directory_exist(self, directory_path: Path):
        """Check if a directory exists on the remote machine."""
        debug("Client.does_remote_directory_exist(): Starting function...")
        if self.remote_os_type != OSType.POSIX:
            debug("Client.does_remote_directory_exist(): Cannot check the directory size on a unsupported OS.")
            return

        command = ""
        if self.remote_os_type == OSType.POSIX:
            command = f"test -d \"{str(directory_path)}\""
        else:
            # Format the result for windows: NOT TESTED YET.
            windows_path = PureWindowsPath(directory_path)
            command = f"""
            @echo off
            IF exist {str(windows_path)} ( echo 0 )
            ELSE ( echo 1 )"
            """
            pass

        # Now return the result.
        try:
            result: Result = self.ssh_connection.run(command, shell=self.remote_shell_name, hide=True)
        except UnexpectedExit as exception:
            exception_argument_list = exception.__str__().split("\n\n")
            invalid_command = exception_argument_list[1].split(":")[1]
            error_code = exception_argument_list[2].split(":")[1]

            debug(f"Client.does_remote_directory_exist(): Received Unexpected Exit Code {error_code} when "
                  f"executing {invalid_command}. Returning False.")
            return False

        # TODO: Handle SSH Exceptions gracefully (Test this by running sudo shutdown "+3" on the remote machine)

        result_code = result.exited
        return result_code is not None and result_code == 0

    def does_local_directory_exist(self, directory_path: Path):
        """Check if the local directory exists."""
        return directory_path.exists()

    def create_remote_root_directory(self, directory_path):
        """Create the remote_root_main_directory if it does not exist."""
        debug("Client.create_root_remote_directory(): Starting function...")
        if self.remote_os_type != OSType.POSIX:
            debug("Client.create_root_remote_directory(): Cannot check the directory size on a unsupported OS.")
            return False

        command = ""
        if self.remote_os_type == OSType.POSIX:
            command = f"mkdir -p \"{str(directory_path)}\""
        else:
            pass

        try:
            self.ssh_connection.run(command, shell=self.remote_shell_name, hide=True)
        except UnexpectedExit as exception:
            exception_argument_list = exception.__str__().split("\n\n")
            invalid_command = exception_argument_list[1].split(":")[1]
            error_code = exception_argument_list[2].split(":")[1]

            error(f"Client.create_root_remote_directory(): Unable to create directory {str(directory_path)}"
                  f"while executing {invalid_command} since it returned {error_code}")
            return False

        # TODO: Handle SSH Exceptions gracefully (Test this by running sudo shutdown "+3" on the remote machine)

        # Now return the result.
        debug(f"Client.create_root_remote_directory(): Created remote directory {str(directory_path)}")
        return True

    def create_local_root_directory(self, directory_path: Path):
        """Create the local root directory if it does not exist."""
        directory_path.mkdir(exist_ok=True)
