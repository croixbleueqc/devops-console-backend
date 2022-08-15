#!/usr/bin/env bash

set -eu -o pipefail

cd "$(dirname "$0")"

python devops_console/init_db.py
