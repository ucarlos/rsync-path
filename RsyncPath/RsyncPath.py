# ------------------------------------------------------------------------------
# Created by Ulysses Carlos on 12/28/2020 at 03:46 PM
#
# RsyncPath.py
# A Python module that can handle rsync a group of directories from a source
# ip address to destination ip with a specified path.
# ------------------------------------------------------------------------------

from . import Client
from . import TransferDirection
from pathlib import Path
from shlex import split
import logging
import subprocess

MIN_SUBDIRECTORY_THRESHOLD = 40
MAX_SUBDIRECTORY_THRESHOLD = 101


class RsyncPath(object):
    """A Thin Wrapper around Rsync that handles threshold values.

    This is to prevent Rsync from wiping a destination path if the source
    path mysteriously becomes empty due to an OS reinstall, new Hard Drive,
    etc...
    """

    def __init__(self,
                 source_dict: dict[str, object] = None,
                 destination_dict: dict[str, object] = None,
                 threshold_dict: dict[str, object] = None,
                 transfer_direction: TransferDirection.TransferDirection = None,
                 debug_mode=False):
        """Construct the object.

        :param: self pointer to current object
        :param: source_dict Dictionary containing information about the source computer.
        :param: destination_dict Dictionary containing information about the destination computer.

        :param: threshold_dict Dictionary that should only contain two keys. An enable_copy_threshold key determines
        if a threshold percentage will be used to compare directory sizes between local and remote machines.
        Disabling this will cause the program to run exactly like rsync.  A subdir_copy_threshold key determines the
        percentage used to compare directory sizes between local and remote machines. The directory size is converted
        into percentage values to be compared to the subdir_copy_threshold. If the directory size is less than the
        subdir_copy_threshold percentage, then the changes done to a directory will NOT be copied over from local to
        remote machine OR remote machine to local machine to prevent accidental deletion if the directory is
        truncated, does not exist, etc.

        :param: transfer_directory The direction of the Rsync Transfer from a remote machine to a local machine or
        from a local machine to a remote machine.

        :param: debug_mode Enable Debug Mode for Testing

        """
        self.local_machine_dict = source_dict
        self.local_username = self.local_machine_dict.get('local_username', None)
        self.local_machine_ip_list = self.local_machine_dict.get("local_machine_ip_list", None)
        self.local_machine_root_path = self.local_machine_dict.get('source_ip_path', None)
        self.local_machine_directory_list = self.local_machine_dict.get('source_directory_list', None)

        self.remote_machine_dict = destination_dict
        self.remote_username: str = self.remote_machine_dict.get('remote_username', None)
        self.remote_machine_ip_list = self.remote_machine_dict.get('remote_machine_ip_list', None)
        self.remote_machine_root_path = self.remote_machine_dict.get('remote_machine_root_path', None)
        self.remote_machine_directory_list = self.remote_machine_dict.get('remote_machine_directory_list', None)

        self.enable_copy_threshold = threshold_dict.get("enable_copy_threshold", True)
        self.subdir_copy_threshold = float(threshold_dict.get("copy_threshold_limit", 0))

        # Throw exception if threshold is not in range [MIN_SUBDIR_THRESHOLD, MAX_SUBDIR_THRESHOLD]:

        self.debug_mode = debug_mode

        if self.debug_mode:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.info("Note: Logging has been disabled.")

        self.transfer_direction = transfer_direction if transfer_direction else None

        if not self.transfer_direction:
            # Attempt to automatically determine the transfer direction:
            self.transfer_direction = TransferDirection.determine_transfer_direction(self.local_machine_ip_list,
                                                                                     self.remote_machine_ip_list)
            if self.transfer_direction == TransferDirection.TransferDirection.ERROR:
                raise RuntimeError("Error: Cannot determine Transfer Direction.")

        if self.is_invalid_object():
            raise Exception("Error: Object cannot contain a value of None.")

        if TransferDirection.TransferDirection.COPY_FROM_REMOTE_TO_LOCAL:
            passed_machine_list = self.remote_machine_ip_list
            passed_username = self.remote_username
        else:
            passed_machine_list = self.local_machine_ip_list
            passed_username = self.local_username

        if passed_username is None:
            self.ssh_client = Client.create_instance_from_available_hostnames(passed_machine_list)
        else:
            self.ssh_client = Client.create_instance_from_username_and_available_hostnames(passed_username,
                                                                                           passed_machine_list)

    def check_if_machine_list_contains_valid_key(self, machine_ip_list: list[dict], key_name):
        for machine_ip in machine_ip_list:
            if machine_ip[key_name] is None or len(machine_ip[key_name]) == 0:
                return False
        return True

    def is_rsync_data_invalid(self):

        """Check if the passed local and remote data variables are valid."""
        # If we are copying from remote to local, remote has to be defined this way:
        # Check the remote dict is valid:

        if self.enable_copy_threshold is True:
            if int(self.subdir_copy_threshold) not in range(MIN_SUBDIRECTORY_THRESHOLD, MAX_SUBDIRECTORY_THRESHOLD):
                raise Exception(f"Error: {self.subdir_copy_threshold} is outside the valid threshold of "
                                f"[{MIN_SUBDIRECTORY_THRESHOLD}, {MAX_SUBDIRECTORY_THRESHOLD - 1}]")

        if self.transfer_direction == TransferDirection.TransferDirection.COPY_FROM_REMOTE_TO_LOCAL:
            source_machine_ip_list = self.remote_machine_ip_list
            source_machine_root_path = self.remote_machine_root_path
            source_machine_directory_list = self.remote_machine_directory_list
            source_username = self.remote_username
            dest_machine_root_path = self.local_machine_root_path
        else:
            source_machine_ip_list = self.local_machine_ip_list
            source_machine_root_path = self.local_machine_root_path
            source_machine_directory_list = self.local_machine_directory_list
            source_username = self.local_username
            dest_machine_root_path = self.remote_machine_root_path



        if self.transfer_direction == TransferDirection.TransferDirection.COPY_FROM_REMOTE_TO_LOCAL:

            if len(self.remote_machine_ip_list) < 1:
                raise RuntimeError("Error: There should be at least a single remote IP in the list of Remote Machine "
                                   "IPs.")

            if self.remote_machine_root_path is None:
                raise RuntimeError("Error: The Remote Machine Root Path should be defined.")

            if len(self.remote_machine_directory_list) < 1:
                raise RuntimeError("Error: There should be at least a single directory path in the list of Remote "
                                   "Directory Path list.")

            machine_list_contains_username = self.check_if_machine_list_contains_valid_key(self.remote_machine_ip_list,
                                                                                           "username")

            if (self.remote_username is None or len(self.remote_username) == 0) and not machine_list_contains_username:
                raise RuntimeError("Error: There should be a Remote Username defined as a variable or as a key in the "
                                   "Remote Machine IP List.")

            if self.local_machine_root_path is None:
                raise RuntimeError("Error: There should be a Remote Username defined as a variable or as a key in the "
                                   "Remote Machine IP List.")

            # First, is the list of remote ip machines at least one?
            # Next, is the remote root Path defined?
            # Is there at least a single remote directory in the directory_path_list
            # Is there a remote username or does the ip machine list contain a username that isn't empty?
            # Does the local list have a local root path defined?
            pass
        else: # if self.transfer_direction == TransferDirection.TransferDirection.COPY_FROM_REMOTE_TO_LOCAL:
            # First, is the list of local ip machines at least one?
            # Next, is the local root Path defined?
            # Is there at least a single local directory in the directory_path_list
            # Is there a local username or does the ip machine list contain a username that isn't empty?
            # Does the remote list have a local root path defined?
            pass

    def __rsync_directories(self, DEBUG_MODE=False, TEST_RUN=False):
        """Copy local directories to a remote path OR Copy remote directories to a local path"""
        logging.info("self.rsync_directories(): Starting Rsync.")

        dry_run_string = "--dry-run" if DEBUG_MODE else ""

        # First, what list are we using here?
        # If we're copying from a list of remote machines to a local machine, We use a list of remote directories
        # to copy over to a local machine. Otherwise, we use a list of local directories to copy over to
        # a remote machine.

        if self.transfer_direction == TransferDirection.TransferDirection.COPY_FROM_REMOTE_TO_LOCAL:
            # Make sure that destination path exists:
            self.ssh_client.create_local_root_directory(self.remote_machine_directory_list)
            copying_directory_list = self.remote_machine_directory_list
            dest_machine_root_path = self.local_machine_root_path
            source_machine_root_path = self.remote_machine_root_path
        else:  # if self.transfer_direction == TransferDirection.TransferDirection.COPY_FROM_LOCAL_TO_REMOTE:
            self.ssh_client.create_remote_root_directory(self.remote_machine_directory_list)
            copying_directory_list = self.local_machine_directory_list
            source_machine_root_path = self.local_machine_root_path
            dest_machine_root_path = self.remote_machine_root_path

        hostname = self.ssh_client.hostname
        username = self.ssh_client.username
        # self.destination_ip_path.mkdir(exist_ok=True)

        # What list are we using here?
        for path in copying_directory_list:
            source_path = source_machine_root_path / path

            # I now realize that this doesn't work the way I think it does.
            # In fact, this doesn't even work since you can't check it using destination_path though SSH.
            # TODO: Create an SSH Client that does this confirmation and size check so that this can work with
            # both Windows and Linux/Posix.
            # destination_path = Path(self.remote_machine_directory_list / path)
            destination_path = Path(dest_machine_root_path / path)

            full_source_path = f"\"{source_path}\""
            full_dest_path = f"{str(self.remote_username)}@{str(self.remote_machine_ip_list)}:\"{str(self.remote_machine_directory_list)}\""

            if self.transfer_direction == TransferDirection.TransferDirection.COPY_FROM_REMOTE_TO_LOCAL:
                full_source_path = f"{str(username)}@{str(hostname)}:\"{source_path}\""
                full_dest_path = f"\"{dest_machine_root_path}\""
                does_dest_path_exist = self.ssh_client.does_remote_directory_exist(destination_path)
            else:  # if self.transfer_direction == TransferDirection.COPY_FROM_LOCAL_TO_REMOTE:
                full_source_path = f"\"{source_path}\""
                full_dest_path = f"{str(username)}@{str(hostname)}:\"{destination_path}\""
                does_dest_path_exist = self.ssh_client.does_local_directory_exist(destination_path)

            rsync_command = f"rsync -aLvzh --delete {dry_run_string} --safe-links {full_source_path} {full_dest_path}"

            # Copy automatically if destination path does not exist
            # or Copy threshold is Disabled.
            if (not does_dest_path_exist) or not self.enable_copy_threshold:
                logging.debug(f"self.rsync_directories(): Preparing to call {rsync_command}")
                if not TEST_RUN:
                    subprocess.run(split(rsync_command))
            else:
                # Compare source and destination directories
                check, backup_size, temp_size = self.verify_directory(source_path, destination_path, self.debug_mode)
                mb_temp_size = round((temp_size / (1 << 20)), 3)
                mb_backup_size = round((backup_size / (1 << 20)), 3)
                if not check:
                    print(f"Warning: Cannot move {str(path)} to {str(destination_path)} Since it is not at least "
                          f"{str(mb_backup_size)}M (Source Size is {str(mb_temp_size)}M)")
                else:
                    print(f"{str(path)} is at least {str(mb_backup_size)}M (Source Size is {str(mb_temp_size)}M) ")
                    logging.debug(f"self.rsync_directories(): Preparing to call {rsync_command}")
                    logging.debug(f"Split command: {split(rsync_command)}")
                    if not TEST_RUN:
                        subprocess.run(split(rsync_command))

        logging.info("self.rsync_directories(): Finished function call.")

    def run(self):
        """Select an available connection and copies over specified source directories to the destination directory."""
        self.__rsync_directories()

    def dry_run(self):
        """Test each source directory with the destination directory, comparing the size. This DOES NOT copy the
        directory.
        """
        self.__rsync_directories(self.debug_mode, True)

    def verify_directory(self, source_dir, dest_dir, DEBUG_MODE=False):
        """Determine if the contents of the temp directory is empty or smaller than the threshold defined in
        subdir_copy_threshold.
        """
        logging.info(f"self.verify_directory(): Verifying {str(source_dir)} and {str(dest_dir)}")
        threshold_percentage = self.subdir_copy_threshold / 100

        # if self.transfer_direction == TransferDirection.TransferDirection.COPY_FROM_REMOTE_TO_LOCAL:
        #    minimum_local_size = threshold_percentage * self.ssh_client.get_local_directory_size_in_bytes(dest_dir)
        #    destination_directory_size = self.ssh_client.get_remote_directory_size_in_bytes(source_dir)
        # else:
        #    minimum_local_size = threshold_percentage * self.ssh_client.get_local_directory_size_in_bytes(source_dir)
        #    destination_directory_size = self.ssh_client.get_remote_directory_size_in_bytes(dest_dir)

        minimum_local_size = threshold_percentage * self.ssh_client.get_local_directory_size_in_bytes(source_dir)
        destination_directory_size = self.ssh_client.get_remote_directory_size_in_bytes(dest_dir)

        if DEBUG_MODE:
            logging.debug(f"self.verify_directory(): Backup Size: {minimum_local_size} bytes")
            debug_message = f"self.verify_directory(): Source Directory: {str(source_dir)} \tDestination Directory : {str(dest_dir)}"
            logging.debug(debug_message)
            logging.debug(f"self.verify_directory(): Destination Directory Size is {destination_directory_size}")

        return ((float(destination_directory_size) >= minimum_local_size), minimum_local_size,
                float(destination_directory_size))
