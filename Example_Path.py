# -----------------------------------------------------------------------------
# Created by Ulysses Carlos on 12/29/2020 at 08:43 PM
#
# Example_Path.py
#
# -----------------------------------------------------------------------------
from pathlib import Path
from rsync_path import RsyncPath as rsync_path



if __name__ == "__main__":
    source_user = "USERNAME"
    source_ip_list = ["SOURCE_IP"]
    source_ip_path = Path(Path.home().root)
    source_directory_list = ["Example Folder"]
    destination_user = "DEST_USERNAME"
    destination_ip = "DEST_IP"
    destination_ip_path = Path.home() / "Downloads"
    subdir_copy_threshold = 85.0

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
    nameless_path = rsync_path(source_user,
                               source_ip_list,
                               source_ip_path,
                               source_directory_list,
                               destination_user,
                               destination_ip,
                               destination_ip_path,
                               subdir_copy_threshold)

    # nameless_path.run()
