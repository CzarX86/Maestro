#!/usr/bin/env python3
"""
Demo script entry point - uses the main demo module.
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from maestro.demo import main

if __name__ == "__main__":
    main()