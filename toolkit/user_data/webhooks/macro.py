#!/usr/bin/env python3

"""
Template for webhook creation
- replies with basic response message
Example: http://10.0.1.61:5000/webhooks/template
"""

import sys, os
SCRIPT_NAME = os.path.basename(sys.argv[0])
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
SCRIPT_ARGS = sys.argv[1:]
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(SCRIPT_DIR)), "lib"))
import macroScript

WORKDIR = os.environ.get("MACRO_WORKDIR", None)
if WORKDIR is None:
    WORKDIR = SCRIPT_DIR

print(f"MacroHooks {SCRIPT_NAME} script, set workdir with MACRO_WORKDIR env. var.")

def search_macros():
    contents = [ f.split('.')[0] for f in os.listdir(WORKDIR) if f.endswith(".macro") ]
    return contents


def run(name):
    executor = macroScript.Executor()
    macro_path = os.path.join(WORKDIR, f"{name}.macro")
    executor.run_micro_script(macro_path)


def main():
    macro_list = search_macros()
    if len(SCRIPT_ARGS) == 0:
        print(f"Available macros: {macro_list}")
    elif SCRIPT_ARGS[0] in macro_list:
        run(SCRIPT_ARGS[0])
    else:
        print("Macro not exists")


############## MAIN ##############
main()
