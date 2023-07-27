# ------------------------------------------------------------------------------
# Created by Ulysses Carlos on 03/20/2021 at 12:19 AM
#
# setup.py
#
# ------------------------------------------------------------------------------

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    "description": "A Python application which wraps around rsync to enable backups with a specified threshold. ",
    "author": "Ulysses Carlos",
    "url": "N/A",
    "download_url": "https://github.com/ucarlos/rsync-path",
    "author_email": "ulysses_carlos@protonmail.com",
    "version": "1.0.0",
    "install_requires": ['fabric'],
    "packages": ['RsyncPath'],
    "scripts": [],
    "name": "rsync_path"
    # test
}


setup(**config)
