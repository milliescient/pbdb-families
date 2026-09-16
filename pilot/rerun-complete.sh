#!/usr/bin/env bash
# Refit every pilot family with a complete record: 40M generations, then the families below
# ESS 200 on any rate again at 160M with a longer burnin, their 40M logs kept aside.
# An optional process group to wait for keeps it off cores another job is using.
#
#   setsid nohup bash rerun-complete.sh [WAIT_PGID] > rerun-complete.out 2>&1 < /dev/null &
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
cd "$HERE" || exit 1
echo $$ > rerun-complete.pgid

if [ -n "${1:-}" ]; then
  echo "waiting for process group $1 $(date -Is)"
  while kill -0 -"$1" 2>/dev/null; do sleep 60; done
fi

export RB=/research/phyloworks/revbayes/projects/cmake/build-matched/rb
export OUT=$HERE/output.complete AUX=$HERE/aux.complete
echo "=== rb $(strings "$RB" | grep -m1 -E '^[A-Za-z0-9._-]+-[0-9]+-g[0-9a-f]{6,}$'), pbdb-families $(git rev-parse --short HEAD), start $(date -Is)"

bash run.sh 40000000 10

python3 - <<'EOF'
import os, shutil
import numpy as np

def ess(x):
    x = np.asarray(x, float); n = len(x); x = x - x.mean()
    v = np.correlate(x, x, "full")[n - 1:] / n
    if v[0] <= 0: return 0.0
    r = v / v[0]; s, t = 0.0, 1
    while t + 1 < n:
        p = r[t] + r[t + 1]
        if p <= 0: break
        s += p; t += 2
    return n / (1 + 2 * s)

out, aside = "output.complete", "output.complete.40M"
os.makedirs(aside, exist_ok=True)
lines = open("sample.tsv").read().splitlines()
keep = [lines[0]]
for row in lines[1:]:
    fam = row.split("\t")[0]
    p = f"{out}/{fam}.log"
    if not os.path.exists(p):
        continue
    hdr = open(p).readline().rstrip("\n").split("\t")
    a = np.loadtxt(p, delimiter="\t", skiprows=1, ndmin=2,
                   usecols=[hdr.index(c) for c in ("lambda", "mu", "psi", "lambda_a")])
    a = np.log(a[int(a.shape[0] * 0.25):])
    if min(ess(a[:, j]) for j in range(4)) < 200:
        keep.append(row)
        shutil.move(p, f"{aside}/{fam}.log")
open("rerun-complete.tsv", "w").write("\n".join(keep) + "\n")
print(f"{len(keep) - 1} families below ESS 200, logs moved to {aside}")
EOF

if [ "$(wc -l < rerun-complete.tsv)" -gt 1 ]; then
  echo "=== refitting at 160M $(date -Is)"
  BURNFRAC=10 bash run.sh 160000000 10 "$HERE/rerun-complete.tsv"
fi
echo "=== done $(date -Is)"
