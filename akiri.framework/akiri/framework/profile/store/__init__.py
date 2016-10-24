# Copyright (c) Akiri Solutions, Inc.  All Rights Reserved.
"""
Profiling support for the akiri.framework.
"""
from __future__ import absolute_import
import sys

from .. import logger

class ProfileStore(object):
    """Base class for persisting a collected profile."""
    # pylint: disable=too-few-public-methods
    def save(self, url, entries):
        """Persist the profiling data for this run."""
        pass


class StreamProfileStore(ProfileStore):
    """Write a collected profile to a stream."""
    def __init__(self, stream=None):
        if stream is None:
            self.stream = sys.stderr
        else:
            self.stream = stream

    def format_entry(self, entry):
        """Convert a profiling entry to the version usable by `save()`"""
        # pylint: disable=no-self-use
        record = '[' + "{0:.6f}".format(entry.timestamp) + '] '
        name = entry.name()
        if name:
            record += name + ': '
        return record + entry.event

    def save(self, path_info, entries):
        logger.info('save')
        print >> self.stream, '### ' + path_info + ' ###'
        for entry in entries:
            print >> self.stream, self.format_entry(entry)
