#!/bin/bash
cd "$(dirname "$0")" || exit
source ./.env/bin/activate
cd src
exec python3 main.py
