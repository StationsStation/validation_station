#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This script sets up the broker for the Eightballer validation station.
It checks if the broker executable exists, makes it executable,
"""
import os
import sys
import subprocess
import shutil
import time

def main():
    # Get the current working directory
    current_dir = os.getcwd()

    # Define the path to the broker executable
    broker_path = os.path.join(current_dir, "broker")

    # Check if the broker executable exists
    if not os.path.exists(broker_path):
        print(f"Error: {broker_path} does not exist.")
        sys.exit(1)

    # Make the broker executable
    try:
        subprocess.run(["chmod", "a+x", broker_path], check=True)
        print("Broker configured successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error configuring broker: {e}")
        sys.exit(1)

    # Optionally, you can run the broker to test if it works

if __name__ == "__main__":
    main()
