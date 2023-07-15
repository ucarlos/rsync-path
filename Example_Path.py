# -----------------------------------------------------------------------------
# Created by Ulysses Carlos on 12/29/2020 at 08:43 PM
#
# Example_Path.py
#
# -----------------------------------------------------------------------------
from pathlib import Path
from RsyncPath.RsyncPath import RsyncPath
import argparse
import logging


def run_rsync_path(argument_dict):
    """Create a RsyncPath object and run it."""
    source_user = "USERNAME"
    source_ip_list = ["SOURCE_IP"]
    source_ip_path = Path(Path.home().root)
    source_directory_list = ["Example Folder"]
    destination_user = "DEST_USERNAME"
    destination_ip = "DEST_IP"
    destination_ip_path = Path.home() / "Downloads"
    subdir_copy_threshold = 85.0
    enable_copy_threshold = True

    DEBUG_MODE = argument_dict['debug_mode']

    logging.debug("Example_Path.run_rsync_path():")
    logging.debug(f"Source user: {str(source_user)}")
    logging.debug("Source IP List: " + "\n".join(source_ip_list))
    logging.debug(f"Source IP Path: {str(source_ip_path)}")
    logging.debug("Source Directory List: " + "\n".join(source_directory_list))

    logging.debug(f"\nDestination User: {str(destination_user)}")
    logging.debug(f"Destination IP: {str(destination_ip)}")
    logging.debug(f"Destination IP Path: {str(destination_ip_path)}")
    logging.debug(f"Copy Threshold: {str(subdir_copy_threshold)}")

    nameless_path = RsyncPath(source_user,
                              source_ip_list,
                              source_ip_path,
                              source_directory_list,
                              destination_user,
                              destination_ip,
                              destination_ip_path,
                              enable_copy_threshold,
                              subdir_copy_threshold,
                              DEBUG_MODE)

    if argument_dict['dry_run']:
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
