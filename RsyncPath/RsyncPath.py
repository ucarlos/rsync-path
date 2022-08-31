# ------------------------------------------------------------------------------
# Created by Ulysses Carlos on 12/28/2020 at 03:46 PM
#
# RsyncPath.py
# A Python module that can handle rsync a group of directories from a source
# ip address to destination ip with a specified path.
# ------------------------------------------------------------------------------
from pathlib import Path
import logging
import platform
import subprocess
from shlex import split
from re import sub


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
        if self.debug_mode:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.info("Note: Logging has been disabled.")

        if (self.is_invalid_object()):
            raise Exception("Error: Object cannot contain a value of None.")

    def is_invalid_object(self):
        """Check if the object is valid or not."""
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
        logging.debug("self.choose_connection(): Searching for an available host.")
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
        logging.debug(f"self.get_directory_size(): Getting size of {str(directory_path)}")
        directory = directory_path
        result = sum(f.stat().st_size for f in directory.glob('**/*') if f.is_file())
        logging.debug(f"self.get_directory_size(): Size of {str(directory_path)} is {float(result)}")
        return float(result)

    def rsync_directories(self, DEBUG_MODE=False, TEST_RUN=False):
        """
        Copy source directories to a destination path.
        """

        logging.info("self.rsync_directories(): Starting Rsync.")

        # Make sure that destination path exists.
        self.destination_ip_path.mkdir(exist_ok=True)

        for path in self.source_directory_list:
            source_path = self.source_ip_path / path

            dest_path = Path(self.destination_ip_path / path)

            rsync_command = f"rsync -aLvzh --delete  --safe-links {str(self.source_user)}@{str(self.source_ip)}:\"'{source_path}'\" \"{str(self.destination_ip_path)}/\""

            # Copy automatically if destination path does not exist
            # or Copy threshold is Disabled.
            if (not dest_path.exists()) or not self.enable_copy_threshold:
                logging.debug(f"self.rsync_directories(): Preparing to call {rsync_command}")
                if not TEST_RUN:
                    subprocess.run(split(rsync_command))
            else:
                # Compare source and destination directories
                check, backup_size, temp_size = self.verify_directory(source_path, dest_path, self.debug_mode)
                mb_temp_size = round((temp_size / (1 << 20)), 3)
                mb_backup_size = round((backup_size / (1 << 20)), 3)
                if not check:
                    print(f"Warning: Cannot move {str(path)} to {str(dest_path)} Since it is not at least {str(mb_backup_size)}M (Source Size is {str(mb_temp_size)}M)")
                else:
                    print(f"{str(path)} is at least {str(mb_backup_size)}M (Source Size is {str(mb_temp_size)}M) ")
                    logging.debug(f"self.rsync_directories(): Preparing to call {rsync_command}")
                    logging.debug(f"Split command: {split(rsync_command)}")
                    if not TEST_RUN:
                        subprocess.run(split(rsync_command))

        logging.info("self.rsync_directories(): Finished function call.")

    def run(self):
        self.source_ip = self.choose_connection()
        self.rsync_directories()

    def dry_run(self):
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

        logging.info(f"self.verify_directory(): Verifying {str(source_dir)} and {str(dest_dir)}")
        threshold = self.subdir_copy_threshold / 100
        backup_size = threshold * self.get_directory_size(dest_dir)

        # The threshold is compared through a subprocess:
        user = self.source_user
        host = self.source_ip

        if DEBUG_MODE:
            logging.debug(f"self.verify_directory(): Backup Size: {backup_size} bytes")
            logging.debug(
                f"self.verify_directory(): Source Directory: {str(source_dir)} \tDestination Directory : {str(dest_dir)}")

        ssh_command = f"ssh {user}@{host} \"du -sbL '{str(source_dir)}'\""
        logging.debug(f"Command: {ssh_command}")
        if DEBUG_MODE:
            logging.debug(f"self.verify_directory(): Preparing to call {ssh_command}")

        logging.debug(f"Command Split: {split(ssh_command)}")
        ssh_result = subprocess.Popen(split(ssh_command), stdout=subprocess.PIPE).communicate()
        temp_size = sub(r"[^\d]", "", ssh_result[0].decode('utf-8'))

        if DEBUG_MODE:
            logging.debug(f"self.verify_directory(): Destination Directory Size is {temp_size}")

        return (float(temp_size) >= backup_size), backup_size, float(temp_size)
