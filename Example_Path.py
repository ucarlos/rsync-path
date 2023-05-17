# -----------------------------------------------------------------------------
# Created by Ulysses Carlos on 12/29/2020 at 08:43 PM
#
# Example_Path.py
#
# -----------------------------------------------------------------------------
from pathlib import Path
from RsyncPath.RsyncPath import RsyncPath
import argparse


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

    # print("Source user: " + str(source_user))
    # print("Source ip list:")
    # for item in source_ip_list:
    #     print(item)
    # print("")
    # print("Source ip path: " + str(source_ip_path))
    # print("Source Directory List:")
    # for item in source_directory_list:
    #     print(str(item))
    # print("")
    # print("Destination User: " + str(destination_user))
    # print("Destination IP: " + str(destination_ip))
    # print("Destination IP Path: " + str(destination_ip_path))
    # print("Copy Threshold: " + str(subdir_copy_threshold))

    # print("Now creating the object!")
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

    # You can do a test run through this:

    if argument_dict['dry_run']:
        nameless_path.dry_run()
    else:
        nameless_path.run()

    # Or run the program directly:


# Now run the damn thing.
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", help="Run the Rsync Path as a dry run.", action="store_true")
    parser.add_argument("--debug-mode", help="Enable Debug Mode.", action="store_true")
    args = parser.parse_args()

    argument_dict = {'dry_run': args.dry_run, 'debug_mode': args.debug_mode}
    print(f"{argument_dict}")
    run_rsync_path(argument_dict)
