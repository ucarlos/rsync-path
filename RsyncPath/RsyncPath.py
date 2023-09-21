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
        self.source_dict = source_dict
        self.source_user = self.source_dict.get('source_user', None)
        self.remote_machine_ip_list = self.source_dict.get("remote_machine_ip_list", None)
        self.source_ip_path = self.source_dict.get('source_ip_path', None)
        self.source_directory_list = self.source_dict.get('source_directory_list', None)

        self.destination_dict = destination_dict
        self.destination_user = self.destination_dict.get('destination_user', None)
        self.destination_ip = self.destination_dict.get('destination_ip', None)
        self.destination_ip_path = self.destination_dict.get('destination_ip_path', None)

        self.enable_copy_threshold = threshold_dict.get("enable_copy_threshold", True)
        self.subdir_copy_threshold = float(threshold_dict.get("subdir_copy_threshold", 0))

        # Throw exception if threshold is not in range [MIN_SUBDIR_THRESHOLD, MAX_SUBDIR_THRESHOLD]:
        if self.enable_copy_threshold is True:
            if int(self.subdir_copy_threshold) not in range(MIN_SUBDIRECTORY_THRESHOLD, MAX_SUBDIRECTORY_THRESHOLD):
                raise Exception(f"Error: {self.subdir_copy_threshold} is outside the valid threshold of "
                                f"[{MIN_SUBDIRECTORY_THRESHOLD}, {MAX_SUBDIRECTORY_THRESHOLD - 1}]")

        self.debug_mode = debug_mode

        if self.debug_mode:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.info("Note: Logging has been disabled.")

        if self.is_invalid_object():
            raise Exception("Error: Object cannot contain a value of None.")

        self.transfer_direction = transfer_direction if transfer_direction else None

        if not self.transfer_direction:
            raise RuntimeError("Error: Cannot determine Transfer Direction.")
        
        if self.source_user is None:
            self.ssh_client = Client.create_instance_from_available_hostnames(self.remote_machine_ip_list)
        else:
            self.ssh_client = Client.create_instance_from_username_and_available_hostnames(self.source_user,
                                                                                           self.remote_machine_ip_list)

    def is_invalid_object(self):
        """Check if the object is valid or not."""
        # TODO: I need to revise this:
        variable_list = [
            self.source_user,
            self.remote_machine_ip_list,
            self.source_ip_path,
            self.source_directory_list,
            self.destination_user,
            self.destination_ip,
            self.destination_ip_path,
            self.subdir_copy_threshold
        ]

        for item in variable_list:
            if item is None:
                return True

        return False

    def __rsync_directories(self, DEBUG_MODE=False, TEST_RUN=False):
        """Copy source directories to a destination path."""
        logging.info("self.rsync_directories(): Starting Rsync.")

        dry_run_string = "--dry-run" if DEBUG_MODE else ""
        # Make sure that destination path exists.
        # TODO: Replace this behavior in an SSH Client.

        if self.transfer_direction == TransferDirection.TransferDirection.COPY_FROM_REMOTE_TO_LOCAL:
            self.ssh_client.create_local_root_directory(self.destination_ip_path)
        else:
            self.ssh_client.create_remote_root_directory(self.destination_ip_path)

        # self.destination_ip_path.mkdir(exist_ok=True)

        for path in self.source_directory_list:
            source_path = self.source_ip_path / path

            # I now realize that this doesn't work the way I think it does.
            # In fact, this doesn't even work since you can't check it using dest_path though SSH.
            # TODO: Create an SSH Client that does this confirmation and size check so that this can work with
            # both Windows and Linux/Posix.
            dest_path = Path(self.destination_ip_path / path)

            full_source_path = f"\"{source_path}\""
            full_destination_path = f"{str(self.destination_user)}@{str(self.destination_ip)}:\"{str(self.destination_ip_path)}\""

            if self.transfer_direction == TransferDirection.TransferDirection.COPY_FROM_REMOTE_TO_LOCAL:
                rsync_command = f"rsync -aLvzh --delete {dry_run_string} --safe-links {full_source_path} {full_destination_path}"
                does_dest_path_exist = self.ssh_client.does_remote_directory_exist(dest_path)
            else:  # if self.transfer_direction == TransferDirection.COPY_FROM_LOCAL_TO_REMOTE:
                rsync_command = f"rsync -aLvzh --delete {dry_run_string} --safe-links {full_destination_path} {full_source_path}"
                does_dest_path_exist = self.ssh_client.does_local_directory_exist(dest_path)

            # Copy automatically if destination path does not exist
            # or Copy threshold is Disabled.
            if (not does_dest_path_exist) or not self.enable_copy_threshold:
                logging.debug(f"self.rsync_directories(): Preparing to call {rsync_command}")
                if not TEST_RUN:
                    subprocess.run(split(rsync_command))
            else:
                # Compare source and destination directories
                check, backup_size, temp_size = self.verify_directory(source_path, dest_path, self.debug_mode)
                mb_temp_size = round((temp_size / (1 << 20)), 3)
                mb_backup_size = round((backup_size / (1 << 20)), 3)
                if not check:
                    print(f"Warning: Cannot move {str(path)} to {str(dest_path)} Since it is not at least "
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

        if self.transfer_direction == TransferDirection.TransferDirection.COPY_FROM_REMOTE_TO_LOCAL:
            minimum_local_size = threshold_percentage * self.ssh_client.get_local_directory_size_in_bytes(dest_dir)
            destination_directory_size = self.ssh_client.get_remote_directory_size_in_bytes(source_dir)
        else:
            minimum_local_size = threshold_percentage * self.ssh_client.get_local_directory_size_in_bytes(source_dir)
            destination_directory_size = self.ssh_client.get_remote_directory_size_in_bytes(dest_dir)

        if DEBUG_MODE:
            logging.debug(f"self.verify_directory(): Backup Size: {minimum_local_size} bytes")
            debug_message = f"self.verify_directory(): Source Directory: {str(source_dir)} \tDestination Directory : {str(dest_dir)}"
            logging.debug(debug_message)
            logging.debug(f"self.verify_directory(): Destination Directory Size is {destination_directory_size}")

        return ((float(destination_directory_size) >= minimum_local_size), minimum_local_size,
                float(destination_directory_size))
