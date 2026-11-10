#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PYTHON="${PYTHON:-python3}"
"$PYTHON" -I -c 'import sys; assert sys.version_info >= (3,11), "Python 3.11+ required"'
"$PYTHON" -I -m venv .venv
VPY="$PWD/.venv/bin/python"
[ -x "$VPY" ] || VPY="$PWD/.venv/Scripts/python.exe"
"$VPY" -I -m pip install -r requirements.txt
"$VPY" -I -m pip check
# -I ignores PYTHONOPTIMIZE; no -O/-OO is used, so assertions remain enabled.
"$VPY" -I -u verify_u2_all.py --output-dir "${1:-reproduced-certificates}"
