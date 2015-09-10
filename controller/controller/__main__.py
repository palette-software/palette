""" Script execution of the module """
# pylint: enable=missing-docstring,relative-import
import sys
import os

from .controller import main

try:
    sys.exit(main())
except KeyboardInterrupt:
    print "\nInterrupted.  Exiting."
    # pylint: disable=protected-access
    os._exit(1)
