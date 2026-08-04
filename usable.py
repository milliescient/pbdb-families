#!/usr/bin/env python3
"""How many families carry enough record to fit a range model, under several readings of enough.

    python3 usable.py

A range model wants ranges. A species seen once is a point, and contributes to the birth and
death rates but tells the sampling rate almost nothing, since the sampling rate is identified
by repeat observation within a species. So family size alone overstates what is fittable, and
the second column below is the one that matters.
"""
import collections
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "taxa"


def scan():
    rows = []
    for p in sorted(OUT.glob("*.tsv")):
        occ = collections.Counter()
        lo, hi = float("inf"), float("-inf")
        extant = 0
        for ln in p.read_text().splitlines()[1:]:
            if not ln.strip():
                continue
            t, a, b, st = ln.split("\t")
            occ[t] += 1
            lo, hi = min(lo, float(a)), max(hi, float(b))
            if st == "extant":
                extant += 1
        ranged = sum(1 for t in occ if occ[t] > 1)
        rows.append(dict(family=p.stem, species=len(occ), occurrences=sum(occ.values()),
                         ranged=ranged, span=hi - lo, singletons=len(occ) - ranged))
    return rows


def main():
    rows = scan()
    tot_f, tot_o = len(rows), sum(r["occurrences"] for r in rows)
    print(f"{tot_f} families, {tot_o} occurrences, "
          f"{sum(r['species'] for r in rows)} species\n")

    sing = sum(r["singletons"] for r in rows)
    spp = sum(r["species"] for r in rows)
    print(f"species seen exactly once: {sing} of {spp} ({100 * sing / spp:.0f}%)\n")

    print(f"{'criterion':<44} {'families':>9} {'occurrences':>12} {'% of occ':>9}")

    def line(label, keep):
        k = [r for r in rows if keep(r)]
        o = sum(r["occurrences"] for r in k)
        print(f"{label:<44} {len(k):>9} {o:>12} {100 * o / tot_o:>8.0f}%")

    line("any species-level record", lambda r: True)
    line("10+ species", lambda r: r["species"] >= 10)
    line("10+ species with a range (2+ occurrences)", lambda r: r["ranged"] >= 10)
    line("10+ ranged species and 20 Myr of span", lambda r: r["ranged"] >= 10 and r["span"] >= 20)
    line("20+ ranged species", lambda r: r["ranged"] >= 20)
    line("20+ ranged species and 30 Myr of span",
         lambda r: r["ranged"] >= 20 and r["span"] >= 30)
    line("50+ ranged species", lambda r: r["ranged"] >= 50)

    fit = [r for r in rows if r["ranged"] >= 10 and r["span"] >= 20]
    fit.sort(key=lambda r: -r["ranged"])
    print(f"\nthe 10+ ranged and 20 Myr set: {len(fit)} families, "
          f"{sum(r['species'] for r in fit)} species, "
          f"{sum(r['occurrences'] for r in fit)} occurrences")
    med = sorted(r["occurrences"] / r["species"] for r in fit)[len(fit) // 2]
    print(f"  median occurrences per species within them: {med:.1f}")
    print(f"  largest: " + ", ".join(f"{r['family']} ({r['ranged']})" for r in fit[:5]))


if __name__ == "__main__":
    main()
