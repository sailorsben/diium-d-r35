#!/bin/sh
# Private ROM reconstruction uses the existing Windows numpy environment.
: "${D35_FF6_PYTHON:?Set D35_FF6_PYTHON to the private Python executable with numpy}"
exec "$D35_FF6_PYTHON" -X utf8 -c "import sys,runpy;sys.path[:0]=['tools','tools/romtools'];runpy.run_path(sys.argv.pop(1),run_name='__main__')" "$@"
