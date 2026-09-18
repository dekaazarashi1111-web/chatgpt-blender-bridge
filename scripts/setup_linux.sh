#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root_dir"

command -v python3 >/dev/null
command -v git >/dev/null
command -v gh >/dev/null

if [[ ! -f config.json ]]; then
  cp config.example.json config.json
fi

python3 bridge_cli.py doctor
python3 bridge_cli.py validate

echo "SETUP=PASS root=$root_dir"
