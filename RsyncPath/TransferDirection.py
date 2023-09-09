#!/usr/bin/env python3
# -------------------------------------------------------------------------------
# Created by Ulysses Carlos on 09/09/2023 at 12:11 AM
#
# TransferDirection.py
#
# -------------------------------------------------------------------------------

from enum import Enum


class TransferDirection(Enum):
    """Simple Enum to determine the Rsync Transfer direction. This basically means whether we are running the script
    on a machine that runs rsync to transfer directories FROM a remote directory or if we are running the script on a
    machine that runs rsync to transfer directories TO a remote directory."""
    COPY_FROM_REMOTE_TO_LOCAL = 0,
    COPY_FROM_LOCAL_TO_REMOTE = 1
