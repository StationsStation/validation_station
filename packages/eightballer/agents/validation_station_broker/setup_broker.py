#!/usr/bin/env python
"""This script sets up the broker for the Eightballer validation station.
It checks if the broker executable exists, makes it executable,.
"""

import os
import sys
import subprocess
from pathlib import Path


def main():
    """Main function to set up the broker."""
    current_dir = os.getcwd()

    broker_path = os.path.join(current_dir, "broker")

    if not Path(broker_path).exists():
        sys.exit(1)

    try:
        subprocess.run(["chmod", "a+x", broker_path], check=True)
    except subprocess.CalledProcessError:
        sys.exit(1)


if __name__ == "__main__":
    main()
