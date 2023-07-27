#!/usr/bin/env python3
# -------------------------------------------------------------------------------
# Created by Ulysses Carlos on 07/26/2023 at 06:44 PM
#
# OSType.py
#
# -------------------------------------------------------------------------------

from enum import Enum
from os import name


class OSType(Enum):
    """Simple Enum for the type of OS that is running on the remote machine."""

    POSIX = 0
    WINDOWS = 1
    UNKNOWN = 2

    @classmethod
    def get_os_type(cls) -> Enum:
        """Retrieve the system type from the OS and map it to the OSType Enum."""
        system_name = name.lower()

        if system_name == "posix":
            return OSType.POSIX
        elif system_name == "nt":
            return OSType.WINDOWS
        else:
            return OSType.UNKNOWN
