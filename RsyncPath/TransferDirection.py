#!/usr/bin/env python3
# -------------------------------------------------------------------------------
# Created by Ulysses Carlos on 09/09/2023 at 12:11 AM
#
# TransferDirection.py
#
# -------------------------------------------------------------------------------

from enum import Enum


def determine_transfer_direction(source_ip_list_dict: list, destination_ip_list_dict: list):
    """Attempt to determine the transfer direction by examining the Source IP List and Destination IP List."""
    source_ip_list_dict_length = len(source_ip_list_dict)
    destination_ip_list_dict_length = len(destination_ip_list_dict)

    if source_ip_list_dict_length > 1 and destination_ip_list_dict_length > 1:
        return TransferDirection.ERROR

    if source_ip_list_dict_length == 1 and destination_ip_list_dict_length == 1:
        return TransferDirection.ERROR

    if source_ip_list_dict_length > 1:
        return TransferDirection.COPY_FROM_REMOTE_TO_LOCAL
    else:
        return TransferDirection.COPY_FROM_LOCAL_TO_REMOTE


class TransferDirection(Enum):
    """Simple Enum to determine the Rsync Transfer direction. This basically means whether we are running the script
    on a machine that runs rsync to transfer directories FROM a remote directory or if we are running the script on a
    machine that runs rsync to transfer directories TO a remote directory.
    """

    COPY_FROM_REMOTE_TO_LOCAL = 0,
    COPY_FROM_LOCAL_TO_REMOTE = 1,
    ERROR = 2
