import sys, os
SCRIPT_NAME = os.path.basename(sys.argv[0])
SCRIPT_ARGS = sys.argv[1:]


print(f"Hello from {SCRIPT_NAME} script, args: {', '.join(SCRIPT_ARGS) if len(SCRIPT_ARGS)>0 else ''}")
