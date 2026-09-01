"""Package entrypoint when invoked via `python -m wia`."""

import sys
from wia.cli.app import main

if __name__ == "__main__":
    sys.exit(main())
