#!/bin/sh
set -eu

python -m evalstack.cli init
if [ "${EVALSTACK_SEED_INCIDENT:-0}" = "1" ]; then
    python -m evalstack.seed
fi
exec python -m evalstack.supervisor
