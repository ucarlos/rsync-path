# ------------------------------------------------------------------------------
# Created by Ulysses Carlos on 12/28/2020 at 03:46 PM
#
# Something.py
# A Python module that can handle rsync a group of directories from a source
# ip address to destination ip with a specified path.
# ------------------------------------------------------------------------------
from pathlib import Path
import platform
import subprocess
import os
import re


class RsyncPath(object):
    """
    A Thin Wrapper around Rsync that handles threshold values.

    This is to prevent Rsync from wiping an destination path if the source
    path  mysteriously becomes empty due to an OS reinstall, new Hard Drive,
    etc...
    """

    # Constructor
    # @param self pointer to current object
    # @param source_user Name of the user on the source computer.
    # @param source_ip_list List of ip addresses that the source can use.
    # @param source_ip_path root directory used by the source computer.
    # @param source_directory_list List of paths to the source directories
    # @param destination_user name of the user on the destination computer.
    # @param destination_ip ip of the destination computer.
    #
    # @param enable_copy_threshold Determine if a threshold percentage will be used.
    #                              Without a threshold percentage, the program will run
    #                              just like rsync.
    #
    # @param subdir_copy_threshold value that is used to determine if a
    #                              source directory has a size equal to or
    #                              more than a percentage of a destination
    #                              directory (if it exists)
    #
    # @param debug_mode Enable Debug Mode for Testing
    def __init__(self,
                 source_user=None,
                 source_ip_list=None,
                 source_ip_path=None,
                 source_directory_list=None,
                 destination_user=None,
                 destination_ip=None,
                 destination_ip_path=None,
                 enable_copy_threshold=True,
                 subdir_copy_threshold=None,
                 debug_mode=False):

        # Throw exception if threshold is not in range [40, 100]

        if enable_copy_threshold is True:
            self.subdir_copy_threshold = float(subdir_copy_threshold)
            if int(self.subdir_copy_threshold) not in range(40, 101):
                raise Exception(f"Error: {self.subdir_copy_threshold} is outside the valid threshold of [40, 100]")

        self.source_user = source_user
        self.source_ip_list = source_ip_list
        self.source_ip_path = source_ip_path
        self.source_directory_list = source_directory_list

        self.destination_user = destination_user
        self.destination_ip = destination_ip
        self.destination_ip_path = destination_ip_path
        self.enable_copy_threshold = enable_copy_threshold
        self.debug_mode = debug_mode

        if (self.is_invalid_object()):
            raise Exception("Error: Object cannot contain a value of None.")

    def is_invalid_object(self):
        """
        Check if the object is valid or not.
        """
        variable_list = [self.source_user,
                         self.source_ip_list,
                         self.source_ip_path,
                         self.source_directory_list,
                         self.destination_user,
                         self.destination_ip,
                         self.destination_ip_path,
                         self.subdir_copy_threshold]

        for item in variable_list:
            if item is None:
                return True

        return False

    def choose_connection(self):
        for i in range(0, len(self.source_ip_list)):
            print(f"Checking if host {i} ({self.source_ip_list[i]}) is available...")
            if self.ping(self.source_ip_list[i]):
                print(f"({self.source_ip_list[i]}) is available!")
                return self.source_ip_list[i]

        raise RuntimeWarning("Could not establish a connection to any "
                             "machine in the IP list. Please check your "
                             "internet connection and make sure the "
                             "other computers are online.")

    def ping(self, ip_address):
        """
        Returns True if host (str) responds to a ping request.
        Remember that a host may not respond to a ping (ICMP) request
        even if the host name is valid.
        """

        # Option for the number of packets as a function of
        os_name = platform.system().lower()

        param = '-n' if os_name == 'windows' else '-c'
        # Choose the null file to send output to:
        # Building the command. Ex: "ping -c 1 google.com"
        command = ['ping', param, '1', ip_address]

        return subprocess.call(command, stdout=subprocess.DEVNULL) == 0

    def get_directory_size(self, directory_path):
        """
        Determine the size of a directory in bytes.
        The size is exactly the same as the size reported by 'du -sb' in Linux.
        """
        directory = directory_path
        result = sum(f.stat().st_size for f in directory.glob('**/*') if f.is_file())
        return float(result)

    def rsync_directories(self, DEBUG_MODE=False, TEST_RUN=False):
        """
        Copy source directories to a destination path.
        """

        # Make sure that destination path exists.
        self.destination_ip_path.mkdir(exist_ok=True)

        for path in self.source_directory_list:

            if DEBUG_MODE:
                print(f"Source IP Path: {self.source_ip_path} ")
            source_path = self.source_ip_path / path
            escaped_path = str(source_path).replace(" ", "\\ ")

            if DEBUG_MODE:
                print(f"Escaped Path: {escaped_path}\n")
            dest_path = Path(self.destination_ip_path / path)


            rsync_command = f"rsync -aLvz --delete {str(self.source_user)}@{str(self.source_ip)}:\"{escaped_path}\" \"{str(self.destination_ip_path)}/\""

            if DEBUG_MODE:
                print(f"Rsync command: {rsync_command}")

            # Copy automatically if destination path does not exist
            # or Copy threshold is Disabled.
            if (not dest_path.exists()) or not self.enable_copy_threshold:
                if not TEST_RUN:
                    os.system(rsync_command)
            else:
                # Compare source and destination directories
                check, backup_size, temp_size = self.verify_directory(escaped_path, dest_path, self.debug_mode)
                mb_temp_size = round((temp_size / (1 << 20)), 3)
                mb_backup_size = round((backup_size / (1 << 20)), 3)
                if not check:
                    print("Warning: Cannot move "
                          + str(path)
                          + " to "
                          + str(dest_path)
                          + " Since it is not at least "
                          + str(mb_backup_size)
                          + "M (Source Size is "
                          + str(mb_temp_size) + "M)")
                else:
                    print(str(path)
                          + " is at least "
                          + str(mb_backup_size)
                          + "M (Source Size is "
                          + str(mb_temp_size) + "M)")
                    if not TEST_RUN:
                        os.system(rsync_command)

    def run(self):
        self.source_ip = self.choose_connection()
        self.rsync_directories()

    def test_run(self):
        """
        Test each source directory with the destination directory,
        comparing the size. This DOES NOT copy the directory.
        """
        self.source_ip = self.choose_connection()
        self.rsync_directories(self.debug_mode, True)

    def verify_directory(self, source_dir, dest_dir, DEBUG_MODE=False):
        """
        Determine if the contents of the temp directory is empty or smaller
        than the threshold defined in subdir_copy_threshold.
        """

        threshold = self.subdir_copy_threshold / 100
        backup_size = threshold * self.get_directory_size(dest_dir)

        if DEBUG_MODE:
            print(f"Backup Size: {backup_size} bytes")
        # The threshold is compared through a subprocess:
        user = self.source_user
        host = self.source_ip

        if DEBUG_MODE:
            test = str(source_dir)
            print(f"Source Directory: {test} ")
            des = str(dest_dir)
            print(f"Destination Directory: {des} ")

        command = 'du -sbL ' + "\"" + str(source_dir) + "\""
        if DEBUG_MODE:
            print(f"Command: {command} ")
            print("ssh {user}@{host} {cmd}".format(user=user, host=host, cmd=command))

        ssh_result = subprocess.Popen("ssh {user}@{host} {cmd}".format(user=user, host=host, cmd=command),
                                      shell=True, stdout=subprocess.PIPE).communicate()

        temp_size = re.sub("[^0-9]", "", ssh_result[0].decode('utf-8'))

        if DEBUG_MODE:
            print(f"Temp Size: {temp_size} ")

        return (float(temp_size) >= backup_size), backup_size, float(temp_size)
