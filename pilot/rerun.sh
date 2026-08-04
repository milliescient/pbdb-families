#!/usr/bin/env bash
# Refit the families in rerun.tsv, the ones below ESS 100 at 40M. Their 40M logs are in
# output.40M/ and are not overwritten. Detached, so it survives the terminal.
#
#   bash rerun.sh        # writes rerun.pgid, kill with: kill -TERM -$(cat rerun.pgid)
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
cd "$HERE"

BURNFRAC=10 setsid nohup bash run.sh 160000000 20 "$HERE/rerun.tsv" \
  > "$HERE/rerun.out" 2>&1 &
echo $! > "$HERE/rerun.pgid"
echo "launched pgid $(cat "$HERE/rerun.pgid"), log $HERE/rerun.out"
