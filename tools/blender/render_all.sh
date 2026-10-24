#!/usr/bin/env bash
# Renders the wagon sprite sources into $1 (default: tools/blender/out). Takes about an hour per wagon on a GPU.
# Usage: tools/blender/render_all.sh [out_dir] [mg|flame|rocket ...]
set -e
cd "$(dirname "$0")/../.."
BLENDER="${BLENDER:-/c/Program Files/Blender Foundation/Blender 5.2/blender.exe}"
OUT="${1:-$(pwd -W 2>/dev/null || pwd)/tools/blender/out}"
shift || true
for variant in ${*:-mg flame rocket}; do
  "$BLENDER" -b --factory-startup -P tools/blender/wagon.py -- "$variant" "$OUT/$variant" > "$OUT/$variant.log" 2>&1
  echo "done: $variant"
done
