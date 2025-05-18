#!/usr/bin/env bash
set -euo pipefail

# Default values
CONFIG=""
GROUP=""
RESOURCES_CONFIG=""
ALL=false

usage() {
  cat <<EOF
Usage: $(basename "$0") [-c config_file] [-g group_name] [-r resources_config_file]

  -c, --config            Path to configuration file
  -g, --group             Group name for downloading resources
  -r, --resources-config  Path to resources config file
  -h, --help              Show this help message
EOF
  exit 1
}

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    -c|--config)
      CONFIG="$2"; shift 2 ;;
    -g|--group)
      GROUP="$2"; shift 2 ;;
    -r|--resources-config)
      RESOURCES_CONFIG="$2"; shift 2 ;;
    -h|--help)
      usage ;;
    --all)
      ALL=true; shift ;;
    *)
      echo "Unknown option: $1"; usage ;;
  esac
done

# Build the python command
cmd=(python3 install.py)

[[ -n "$CONFIG"         ]] && cmd+=(-c        "$CONFIG")
[[ -n "$GROUP"          ]] && cmd+=(-g        "$GROUP")
[[ -n "$RESOURCES_CONFIG" ]] && cmd+=(-r      "$RESOURCES_CONFIG")
[[ "$ALL" == true      ]] && cmd+=(--all)
# Execute
exec "${cmd[@]}"
