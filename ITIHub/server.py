#!/usr/bin/env python
import os
import sys

# Set environment variables for timeouts
os.environ['DAPHNE_HTTP_TIMEOUT'] = '10'  # 10 seconds for HTTP
os.environ['DAPHNE_WEBSOCKET_TIMEOUT'] = '15'  # 15 seconds for WebSockets  
os.environ['DAPHNE_DISCONNECT_TIMEOUT'] = '2'  # 2 seconds for disconnect handlers

from daphne.cli import CommandLineInterface

# Run Daphne with optimized settings
if __name__ == "__main__":
    cli = CommandLineInterface()
    cli.entrypoint(sys.argv[1:])
