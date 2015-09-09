import os
from .controller import main

try:
    main()
except KeyboardInterrupt:
    print "\nInterrupted.  Exiting."
    # pylint: disable=protected-access
    os._exit(1)
