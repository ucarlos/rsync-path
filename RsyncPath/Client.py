# -------------------------------------------------------------------------------
# Created by Ulysses Carlos on 07/15/2023 at 02:25 PM
#
# Client.py
# Simple SSH Client used to execute specific commands on a remote machine.
# -------------------------------------------------------------------------------


from fabric import Connection, Result
from invoke.exceptions import UnexpectedExit
from pathlib import Path, PureWindowsPath, WindowsPath
from shlex import split
from OSType import OSType
from logging import info, debug, error

DEFAULT_SSH_PORT = 22


def get_local_directory_size(directory_path):
    """Determine the size of a directory in bytes."""
    debug(f"Client.get_local_directory_size(): Getting the directory size of {str(directory_path)}")

    size_in_bytes = float(sum(file.stat().st_size for file in directory_path.glob('**/*') if file.is_file()))
    debug(f"Client.get_local_directory_size(): Size of {str(directory_path)} is {size_in_bytes}")
    return size_in_bytes


class Client(object):
    """A simple Client class to execute specific commands on both your local and remote machines."""

    def __init__(self, username, hostname, port=DEFAULT_SSH_PORT, os_type=OSType.UNKNOWN):
        """Construct the Client. Object."""
        self.ssh_connection = Connection(host=hostname, user=username, port=port)
        self.os_type = os_type
        self.shell_name = "/bin/bash" if self.os_type == OSType.POSIX else "cmd.exe"

    def change_connection(self, username, hostname, port, os_type=None):
        """Close the current SSH connection and create a new one using the passed username, hostname and port
        variables.
        """
        if self.ssh_connection.is_connected():
            self.ssh_connection.close()
        self.ssh_connection = Connection(user=username, hostname=hostname, port=port)
        if os_type is not None:
            self.os_type = os_type

    def check_remote_directory_size_in_bytes(self, directory_path):
        """Retrieve the size of a specific directory on the remote machine."""
        debug("Client..check_directory_size(): Starting function...")

        if self.os_type != OSType.POSIX:
            debug("Client.check_remote_directory_size_in_bytes(): Cannot check the directory size on a unsupported "
                  "OS.")
            return

        command = ""
        if self.os_type == OSType.POSIX:
            command = f"du -sLb {str(directory_path)}"
        else:
            pass

        # Now run the damn thing:
        try:
            result = self.ssh_connection.run(command, shell=self.shell_name, hide=True)
        except UnexpectedExit as exception:
            exception_argument_list = exception.__str__().split("\n\n")
            invalid_command = exception_argument_list[1].split(":")[1]
            error_code = exception_argument_list[2].split(":")[1]

            debug(f"Client.check_remote_directory_size_in_bytes(): Received Unexpected Exit Code {error_code} when "
                  f"executing {invalid_command}. Returning None as the byte size.")
            return None

        # Now split the value:
        size_in_bytes = result.stdout.split("\t")[0] if self.os_type == OSType.POSIX else result.stdout
        debug(f"Client.check_remote_directory_size_in_bytes(): Retrieved Exit Code {result.exited}; "
              f"Size of {str(directory_path)} is {size_in_bytes} byte(s)")
        return int(size_in_bytes)

    def check_if_remote_directory_exists(self, directory_path: Path):
        """Check if a directory exists on the remote machine."""
        debug("Client..check_if_directory_exists(): Starting function...")
        if self.os_type != OSType.POSIX:
            debug("Client.check_directory_size(): Cannot check the directory size on a unsupported OS.")
            return

        command = ""
        if self.os_type == OSType.POSIX:
            command = f"test -d {str(directory_path)}"
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
            result = self.ssh_connection.run(command, shell=self.shell_name, hide=True)
        except UnexpectedExit as exception:
            exception_argument_list = exception.__str__().split("\n\n")
            invalid_command = exception_argument_list[1].split(":")[1]
            error_code = exception_argument_list[2].split(":")[1]

            debug(f"Client.check_if_remote_directory_exists(): Received Unexpected Exit Code {error_code} when "
                  f"executing {invalid_command}. Returning False.")
            return False

        result_code = result.exited
        return result_code is not None and result_code == 0

    def create_root_remote_directory(self, directory_path):
        """Create the remote_root_main_directory if it does not exist."""
        debug("Client..create_root_remote_directory(): Starting function...")
        if self.os_type != OSType.POSIX:
            debug("Client.check_directory_size(): Cannot check the directory size on a unsupported OS.")
            return False

        command = ""
        if self.os_type == OSType.POSIX:
            command = f"mkdir -p {str(directory_path)}"
        else:
            pass

        try:
            self.ssh_connection.run(command, shell=self.shell_name, hide=True)
        except UnexpectedExit as exception:
            exception_argument_list = exception.__str__().split("\n\n")
            invalid_command = exception_argument_list[1].split(":")[1]
            error_code = exception_argument_list[2].split(":")[1]

            error(f"Client.create_root_remote_directory(): Unable to create directory {str(directory_path)}"
                  f"while executing {invalid_command} since it returned {error_code}")
            return False

        # Now return the result.
        debug(f"Client..create_root_remote_directory(): Created remote directory {str(directory_path)}")
        return True

    def can_connect_to_remote_machine(self, ip_address: str):
        """Verify that a connection to a remote machine can be made by sending a ping request.
        NOTE: A host may not respond to a ping request even if the ip address is valid.

        :param: ip_address
        :returns True if the remote address responds to the ping request. False otherwise.
        """
        info("Client.ping(): Starting ping call:")

        if self.os_type != OSType.POSIX:
            error("Client.ping(): Cannot make a connection to an remote machine using an unsupported OS Type.")
            return False

        argument = "-n" if self.os_type == OSType.WINDOWS else "-c"
        command = f"ping {argument} 1 {ip_address}"
        command_list = split(command)

        debug(f"Client.ping(): Passing the following command list: {command_list}")
        try:
            result = self.ssh_connection.local(command, shell=self.shell_name, hide=True)
        except UnexpectedExit as exception:
            exception_argument_list = exception.__str__().split("\n\n")
            invalid_command = exception_argument_list[1].split(":")[1]
            error_code = exception_argument_list[2].split(":")[1]

            debug(f"Client.can_connect_to_remote_machine(): Received Unexpected Exit Code {error_code} when "
                  f"executing {invalid_command}. Returning False.")
            return False

        return result.return_code is not None and result.return_code == 0

    @staticmethod
    def create_client_instance_from_available_hostnames(self, username, hostname_list: list, os_type=OSType.UNKNOWN):
        """Select an available client from a hostname list and return a Client instance."""
        debug("Client.select_available_client(): Searching for an available host.")
        index = 1
        for hostname in hostname_list:
            debug(f"Checking if host {index} with address {hostname} is available:")
            if self.can_connect_to_remote_machine(hostname):
                return Client(username, hostname, DEFAULT_SSH_PORT, os_type)
            index += 1

        error_message = """Could not establish any connection to any remote machine on the IP List. Please check your
        internet connection and make sure that at least one of the remote machines is available."""
        raise RuntimeError(error_message)
