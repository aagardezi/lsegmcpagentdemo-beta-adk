# Package marker for the LSEG ADK agent
import os
import sys

# Add project root to sys.path to ensure custom metrics are importable by CLI
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from . import agent
