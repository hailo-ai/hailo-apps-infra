#!/usr/bin/env bash

set -euo pipefail

# Default values
PROJECT_DIR="."
BUILD_MODE="release"
CLEAN=false

usage() {
  cat <<EOF
Usage: $(basename "$0") [-p PROJECT_DIR] [debug|clean|release]

  -p PROJECT_DIR   Path to your project root (default: current dir)
  debug            Do a debug build
  release          Do a release build (default)
  clean            Remove the build directory and exit

Examples:
  $(basename "$0") -p /path/to/myproj debug
  $(basename "$0") clean
EOF
  exit 1
}

# Parse flags
while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--project-dir)
      if [[ -n "${2-}" ]]; then
        PROJECT_DIR="$2"
        shift 2
      else
        echo "Error: --project-dir requires a value" >&2
        usage
      fi
      ;;
    debug|release|clean)
      BUILD_MODE="$1"
      [[ "$1" == "clean" ]] && CLEAN=true
      shift
      ;;
    -h|--help)
      usage
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      ;;
  esac
done

# Verify Meson & Ninja
for cmd in meson ninja; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "Error: '$cmd' is not installed. Please install it and try again." >&2
    exit 1
  fi
done

BUILD_DIR="$PROJECT_DIR/build.$BUILD_MODE"

if [[ "$CLEAN" == true ]]; then
  echo "Cleaning build directory: $BUILD_DIR"
  rm -rf "$BUILD_DIR"
  exit 0
fi

# Create and enter build dir
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# Configure if needed
if [[ ! -f build.ninja ]]; then
  echo "Configuring project at '$PROJECT_DIR' ($BUILD_MODE mode)..."
  meson setup "$PROJECT_DIR" --buildtype="$BUILD_MODE"
else
  echo "Build directory already configured. Skipping meson setup."
fi

# Build & install
echo "Building with ninja..."
ninja -j"$(nproc)"

echo "Installing..."
ninja install

echo "✅ Build completed successfully in '$BUILD_DIR'"
