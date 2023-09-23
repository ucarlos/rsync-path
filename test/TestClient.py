#!/usr/bin/env python3
# -------------------------------------------------------------------------------
# Created by Ulysses Carlos on 09/08/2023 at 09:06 PM
#
# TestClient.py
#
# -------------------------------------------------------------------------------

import logging
from pathlib import Path
from RsyncPath.Client import Client, can_connect_to_remote_machine
from RsyncPath.OSType import OSType

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    current_directory = Path.cwd()
    valid_directory = Path.home() / "Pictures" / "Misc"

    invalid_directory = valid_directory / "aaaa"
    client = Client("localhost", "192.168.1.72", 22, OSType.POSIX)

    # Testing:
    print(f"Does {str(valid_directory)} exist? {client.does_remote_directory_exist(valid_directory)}")
    print(f"Does {str(invalid_directory)} exist? {client.does_remote_directory_exist(invalid_directory)}")

    print(f"Size of {str(valid_directory)} is {client.get_remote_directory_size_in_bytes(valid_directory)} byte(s).")
    print(f"Size of {str(invalid_directory)} is {client.get_remote_directory_size_in_bytes(invalid_directory)} byte(s).")

    can_connect = can_connect_to_remote_machine("192.168.1.73", OSType.POSIX)
    print(f"Can connect to 192.168.1.73? {can_connect}")
