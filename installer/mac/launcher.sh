#!/bin/bash
R="$(cd "$(dirname "$0")/../Resources" && pwd)"
exec "$R/python/bin/python3.12" -s -E "$R/pirimu.py" "$@"
