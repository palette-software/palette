# Copyright (c) Akiri Solutions, Inc.  All Rights Reserved.
""" Reloader functionality to extend that found in paste. """

import os

# Import install so that it can be used from this module.
# pylint: disable=unused-import
from paste.reloader import watch_file, install

def watch_dir(path):
    """ Recursively add a directory to the watch files """
    for dirpath, dirnames, filenames in os.walk(path):
        for name in dirnames:
            watch_dir(os.path.join(dirpath, name))
        for name in filenames:
            watch_file(os.path.join(dirpath, name))
