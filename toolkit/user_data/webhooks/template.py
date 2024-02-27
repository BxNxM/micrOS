#!/usr/bin/env python3

"""
Template for webhook creation
- replies with basic response message
Example: http://10.0.1.61:5000/webhooks/template
"""

import sys, os
SCRIPT_NAME = os.path.basename(sys.argv[0])
SCRIPT_ARGS = sys.argv[1:]


print(f"Hello from {SCRIPT_NAME} script, args: {', '.join(SCRIPT_ARGS) if len(SCRIPT_ARGS)>0 else ''}")
