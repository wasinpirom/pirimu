#!/bin/bash
cd "$(dirname "$0")" || exit 1
if [ ! -x .venv/bin/python ]; then echo "ยังไม่ได้ติดตั้ง กรุณาเปิด install.command ก่อน"; read -r _; exit 1; fi
exec .venv/bin/python pirimu.py
