# -----------------------------------------------------------------------------
# Created by Ulysses Carlos on 12/29/2020 at 08:43 PM
#
# Example_Path.py
#
# -----------------------------------------------------------------------------
from pathlib import Path
from RsyncPath.RsyncPath import RsyncPath
from RsyncPath.OSType import OSType
from RsyncPath.TransferDirection import TransferDirection
import argparse
import logging


def run_rsync_path(parameter_argument_dict):
    """Create a RsyncPath object and run it."""

    # You can either define a specific source user to use for all the remove machines,
    # or place the username in the remote_machine_ip_dict.
    # If you do so, set the source_user variable to None.
    source_user = "USERNAME"
    remote_machine_ip_list = [
        {"username": "USERNAME", "hostname": "SOURCE_IP", "os_type": OSType.UNKNOWN}
    ]

    # Are we copying from a local machine to list of remote machines
    # Or from many possible remote machines to a local machine?
    transfer_direction = TransferDirection.COPY_FROM_LOCAL_TO_REMOTE

    # TODO: I just realized that I might need to reconsider the constructor again to make this more intuitive.
    # again since
    source_ip_path = Path(Path.home().root)
    source_directory_list = ["Example Folder"]
    destination_user = "DEST_USERNAME"
    destination_ip = "DEST_IP"
    destination_ip_path = Path.home() / "Downloads"
    subdir_copy_threshold = 85.0
    enable_copy_threshold = True

    DEBUG_MODE = parameter_argument_dict['debug_mode']

    logging.debug("Example_Path.run_rsync_path():")
    if source_user:
        logging.debug(f"Source user: {str(source_user)}")

    logging.debug(f"Source IP List: {remote_machine_ip_list}")
    logging.debug(f"Source IP Path: {str(source_ip_path)}")
    logging.debug("Source Directory List: " + "\n".join(source_directory_list))

    logging.debug(f"\nDestination User: {str(destination_user)}")
    logging.debug(f"Destination IP: {str(destination_ip)}")
    logging.debug(f"Destination IP Path: {str(destination_ip_path)}")
    logging.debug(f"Copy Threshold: {str(subdir_copy_threshold)}")

    # Now package it all up:
    source_dict = {
        "source_user" : source_user,
        "remote_machine_ip_list": remote_machine_ip_list,
        "source_ip_path": source_ip_path,
        "source_directory_list": source_directory_list
    }

    destination_dict = {
        "destination_user": destination_user,
        "destination_ip": destination_ip,
        "destination_ip_path": destination_ip_path
    }

    threshold_dict = {
        "enable_copy_threshold": enable_copy_threshold,
        "subdir_copy_threshold": subdir_copy_threshold
    }

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

    if argument_dict['debug_mode']:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    run_rsync_path(argument_dict)
