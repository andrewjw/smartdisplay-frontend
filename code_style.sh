#!/bin/bash

set -e

ln -sf `python3 -c "import importlib.util; import os.path; print(os.path.dirname(importlib.util.find_spec('i75', None).origin))"`/emulated emulated

MYPYPATH=./stubs:./emulated:$MYPYPATH mypy -m smartdisplay

MYPYPATH=./stubs:./emulated:$MYPYPATH mypy main.py

${PYCODESTYLE:-pycodestyle} main.py smartdisplay/

rm emulated
