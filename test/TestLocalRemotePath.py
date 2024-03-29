#!/usr/bin/env python3
# -------------------------------------------------------------------------------
# Created by Ulysses Carlos on 09/22/2023 at 10:39 PM
#
# TestLocalRemotePath.py
#
# -------------------------------------------------------------------------------
from pathlib import Path
from RsyncPath.RsyncPath import RsyncPath
from RsyncPath.OSType import OSType
from RsyncPath.TransferDirection import TransferDirection
import argparse
import logging


def run_rsync_path_from_local_to_remote(parameter_argument_dict):
    """Create a RsyncPath object and run it."""
    # If we are copying from a list of local_machines to a single remote machine, do the following:
    # Because we are copying from a list of local machines to a single remote machines,
    # Define the transfer direction like so:
    transfer_direction = TransferDirection.COPY_FROM_LOCAL_TO_REMOTE

    # Next, set your list of local_machines:
    # You can either define a specific local user to use for all the local machines,
    # or place the username in the local_machine_ip_dict.
    # If you do so, set the local_user variable to None.

    local_username = "local_username"
    local_machine_ip_list = None

    # Next, define the list of possible directories on the local machines to copy over the local machine:
    # This is done by defining a root path and list of possible directories in that path:
    local_machine_root_path = Path.home() / "Pictures"
    local_machine_directory_list = [
        "Laser"
    ]

    # Next, define your remote machine:
    remote_username = "remote_username"
    remote_machine_ip_list = None
    remote_machine_root_path = Path.home() / "Pictures"

    # You can either define a specific remote user to use for all the remote machines,
    # or place the username in the local_machine_ip_dict.
    # If you do so, set the local_user variable to None.
    remote_machine_directory_list = None
    remote_machine_ip_list = [
        {"username": "remote_username", "hostname": "192.168.1.92", "os_type": OSType.POSIX}
    ]

    # Now, define the threshold percentage. This defines the minimum directory size percentage that the remote
    # directory should be before it is copied over to the local directory.
    # For example, if a local directory is 100 MiB, and we have a threshold value of 85, the remote directory
    # needs to be at least 85 MiB before it is copied over. This to prevent accidental deletion in cases where
    # the remote directory was deleted, or the script ran on a remote machine that was freshly installed, etc.

    # In order to use the threshold value, you'll need to enable it. Otherwise, it will behave like normal rsync:
    enable_copy_threshold = True
    copy_threshold_limit = 85.0

    # Next, define whether we're using DEBUG MODE or NOT:
    DEBUG_MODE = True

    # Next, pack everything up into local and remote dictionaries:
    source_dict = {
        "source_username": local_username,
        "source_machine_ip_list": local_machine_ip_list,
        "source_machine_root_path": local_machine_root_path,
        "source_machine_directory_list": local_machine_directory_list,
    }

    destination_dict = {
        "destination_username": remote_username if remote_username else None,
        "destination_machine_ip_list": remote_machine_ip_list,
        "destination_machine_root_path": remote_machine_root_path,
        "destination_machine_directory_list": remote_machine_directory_list
    }

    threshold_dict = {
        "enable_copy_threshold": enable_copy_threshold,
        "copy_threshold_limit": copy_threshold_limit
    }

    # Now show the following log statements:
    if logging.getLogger().getEffectiveLevel() == logging.DEBUG:
        total_dict = {}
        total_dict.update(source_dict)
        total_dict.update(destination_dict)

        for key, value in total_dict.items():
            key_label = key.replace("_", " ").title()
            logging.debug(f"{key_label}: {value}")

    # And now, create and run the RsyncPath object:
    nameless_path = RsyncPath(source_dict,
                              destination_dict,
                              threshold_dict,
                              transfer_direction,
                              DEBUG_MODE)

    if parameter_argument_dict['dry_run']:
        nameless_path.dry_run()
    else:
        nameless_path.run()


# Now run the damn thing.
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", help="Run the Rsync Path as a dry run.", action="store_true")
    parser.add_argument("--debug-mode", help="Enable Debug Mode.", action="store_true")
    args = parser.parse_args()

    argument_dict = {'dry_run': args.dry_run, 'debug_mode': args.debug_mode}

    logging.basicConfig(level=logging.DEBUG)

    # Depending on the Transfer direction, either run the RsyncPath from remote to local
    # or from local to remote:
    run_rsync_path_from_local_to_remote(argument_dict)
