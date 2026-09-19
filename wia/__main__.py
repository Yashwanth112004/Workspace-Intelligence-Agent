"""Package entrypoint when invoked via `python -m wia`."""

import sys
from wia.cli.app import cli_entrypoint

if __name__ == "__main__":
    cli_entrypoint()
