#!/usr/bin/env bash
# Fit every family in a sample table, in parallel. Resumable: a family whose log already has
# the full sample count is skipped, so an interrupted run is restarted by rerunning this.
# Refitting a family therefore means moving its log aside first.
#
#   bash run.sh [GENS] [NCORES] [SAMPLE]
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
GENS=${1:-40000000}
NCORES=${2:-20}
SAMPLE=${3:-$HERE/sample.tsv}
BURNFRAC=${BURNFRAC:-20}
PRINTGEN=$((GENS / 2000))
RB=${RB:-/research/phyloworks/revbayes/projects/cmake/build-reporting/rb}
OUT=$HERE/output
AUX=$HERE/aux
mkdir -p "$OUT" "$AUX"
: > "$HERE/failures.log"

fit_one() {
  local fam=$1 young=$2 old=$3
  local log=$OUT/$fam.log
  # 2000 samples plus the header is a finished chain
  if [ -f "$log" ] && [ "$(wc -l < "$log")" -ge 2001 ]; then return 0; fi
  cat > "$AUX/$fam.Rev" <<EOF
DATA = "$HERE/../taxa/$fam.tsv"
OUT  = "$log"
PRESENT = $young
MAXFA   = $old
GENS = $GENS
PRINTGEN = $PRINTGEN
BURNFRAC = $BURNFRAC
source("$HERE/fit.Rev")
EOF
  if ! "$RB" "$AUX/$fam.Rev" < /dev/null > "$AUX/$fam.out" 2>&1; then
    echo "$fam" >> "$HERE/failures.log"
  fi
}
export -f fit_one
export OUT AUX HERE RB GENS PRINTGEN BURNFRAC

echo "fitting $(($(wc -l < "$SAMPLE") - 1)) families from $(basename "$SAMPLE"), \
$GENS generations, burnin GENS/$BURNFRAC, $NCORES cores"
# largest first, so the long tail is not left running alone at the end
tail -n +2 "$SAMPLE" | sort -t$'\t' -k2,2nr \
  | awk -F'\t' '{print $1, $5, $6}' \
  | xargs -P "$NCORES" -n 3 bash -c 'fit_one "$@"' _
echo "done, $(wc -l < "$HERE/failures.log") failures"
