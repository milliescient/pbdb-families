#!/usr/bin/env python3
"""Draw the stratified family sample the pilot fits.

    python3 sample.py [--check]

Wholly extinct families only, so nothing survives to the truncation point and rho = 0 is
exact rather than a guess about how much of an extant fauna PBDB holds. Twenty per size
class, so reading contraction against clade size has even support instead of being dominated
by the small families that make up most of the database.
"""
import argparse
import collections
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
TAXA = HERE.parent / "taxa"
OUT = HERE / "sample.tsv"
SEED = 20260804
PER_BIN = 20
BINS = ((10, 19), (20, 39), (40, 79), (80, 159), (160, 10 ** 6))
MIN_RANGED = 10


def build():
    rows = []
    for p in sorted(TAXA.glob("*.tsv")):
        occ = collections.Counter()
        extant = 0
        lo, hi = float("inf"), float("-inf")
        for ln in p.read_text().splitlines()[1:]:
            if not ln.strip():
                continue
            t, a, b, s = ln.split("\t")
            occ[t] += 1
            lo, hi = min(lo, float(a)), max(hi, float(b))
            if s == "extant":
                extant += 1
        if extant or sum(1 for t in occ if occ[t] > 1) < MIN_RANGED:
            continue
        rows.append(dict(fam=p.stem, sp=len(occ),
                         ranged=sum(1 for t in occ if occ[t] > 1),
                         occ=sum(occ.values()), youngest=lo, oldest=hi))

    random.seed(SEED)
    pick = []
    for lo, hi in BINS:
        c = [r for r in rows if lo <= r["sp"] <= hi]
        pick += random.sample(c, min(PER_BIN, len(c)))
    pick.sort(key=lambda r: r["sp"])
    out = ["family\tspecies\tranged\toccurrences\tyoungest_ma\toldest_ma"]
    out += [f"{r['fam']}\t{r['sp']}\t{r['ranged']}\t{r['occ']}"
            f"\t{r['youngest']:g}\t{r['oldest']:g}" for r in pick]
    return "\n".join(out) + "\n", len(pick), sum(r["occ"] for r in pick)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="compare, do not write")
    args = ap.parse_args()
    text, n, occ = build()
    if args.check:
        same = OUT.exists() and OUT.read_text() == text
        print(f"{OUT.name} {'matches' if same else 'DIFFERS from'} a fresh draw")
        return 0 if same else 1
    OUT.write_text(text)
    print(f"{n} families, {occ} occurrences -> {OUT.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
