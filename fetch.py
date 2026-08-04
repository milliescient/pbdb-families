#!/usr/bin/env python3
"""Every PBDB family with a species-level fossil record, as RevBayes taxon tables.

    python3 fetch.py              # download what is missing, then build
    python3 fetch.py --build      # rebuild the tables from what is already downloaded
    python3 fetch.py --min-species 20

Three bulk queries, not one per family: PBDB streams a whole result set far more cheaply
than it answers fifteen thousand small questions, and the grouping is local anyway.

A species is placed in a family by the occurrence record's own classification, so a taxon
with no occurrences never appears. Ages are the occurrence bounds in Ma, unshifted.
"""
import argparse
import collections
import csv
import datetime
import pathlib
import sys
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
RAW = HERE / "raw"
OUT = HERE / "taxa"
API = "https://paleobiodb.org/data1.2"
UA = {"User-Agent": "pbdb-families/1 (+research use; one bulk query per resource)"}

QUERIES = {
    # every family, with the occurrence and subtaxon counts PBDB already keeps
    "families.tsv": f"{API}/taxa/list.tsv?base_name=Life&rank=family&show=app,size&vocab=pbdb",
    # every occurrence identified to species, carrying its family
    "occurrences.tsv": (f"{API}/occs/list.tsv?base_name=Life&taxon_reso=species"
                        f"&show=class&vocab=pbdb"),
    # the extant species, which is what separates a status of extant from extinct
    "extant.tsv": f"{API}/taxa/list.tsv?base_name=Life&rank=species&extant=yes&vocab=pbdb",
}


def download(name, url):
    """Stream to a .part file so an interrupted download is never mistaken for a complete one."""
    dest = RAW / name
    if dest.exists():
        print(f"  have {name}  {dest.stat().st_size / 1e6:.1f} MB")
        return
    part = dest.with_suffix(dest.suffix + ".part")
    print(f"  get  {name} ...", end="", flush=True)
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=1800) as r, \
            open(part, "wb") as fh:
        n = 0
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            fh.write(chunk)
            n += len(chunk)
            print(f"\r  get  {name} ... {n / 1e6:6.1f} MB", end="", flush=True)
    part.rename(dest)
    print(f"\r  got  {name}  {dest.stat().st_size / 1e6:.1f} MB      ")


def build(min_species):
    extant = set()
    with open(RAW / "extant.tsv", newline="", encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            extant.add(r["taxon_name"].replace(" ", "_"))
    print(f"{len(extant)} extant species")

    # family -> taxon -> list of (min_age, max_age)
    fams = collections.defaultdict(lambda: collections.defaultdict(list))
    nrow = nskip = 0
    with open(RAW / "occurrences.tsv", newline="", encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            nrow += 1
            fam, name = r["family"], r["accepted_name"]
            if r["accepted_rank"] != "species" or not fam or not name:
                nskip += 1
                continue
            try:
                lo, hi = float(r["min_ma"]), float(r["max_ma"])
            except ValueError:
                nskip += 1
                continue
            fams[fam][name.replace(" ", "_")].append((lo, hi))
    print(f"{nrow} occurrences read, {nskip} without a family, species name or age")

    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*.tsv"):
        old.unlink()
    index = []
    for fam in sorted(fams):
        by_taxon = fams[fam]
        if len(by_taxon) < min_species:
            continue
        rows = []
        for taxon in sorted(by_taxon):
            status = "extant" if taxon in extant else "extinct"
            for lo, hi in sorted(by_taxon[taxon]):
                rows.append(f"{taxon}\t{lo:g}\t{hi:g}\t{status}")
        # a family name can carry a space or a slash, neither of which belongs in a path
        safe = fam.replace(" ", "_").replace("/", "-")
        (OUT / f"{safe}.tsv").write_text(
            "taxon\tmin_age\tmax_age\tstatus\n" + "\n".join(rows) + "\n")
        nex = sum(1 for t in by_taxon if t in extant)
        index.append((fam, safe, len(by_taxon), len(rows), nex))

    with open(HERE / "index.tsv", "w") as fh:
        fh.write("family\tfile\tspecies\toccurrences\textant_species\n")
        for row in index:
            fh.write("\t".join(str(x) for x in row) + "\n")
    tot = sum(r[3] for r in index)
    print(f"{len(index)} families with at least {min_species} species, "
          f"{sum(r[2] for r in index)} species, {tot} occurrences -> {OUT.name}/")

    # PBDB is edited continuously, so what came back is a date and a set of counts
    with open(HERE / "manifest.tsv", "w") as fh:
        for k, v in (("fetched", datetime.date.today().isoformat()),
                     ("min_species", min_species),
                     ("occurrences_read", nrow),
                     ("occurrences_skipped", nskip),
                     ("extant_species", len(extant)),
                     ("families_with_occurrences", len(fams)),
                     ("families_written", len(index)),
                     ("species_written", sum(r[2] for r in index)),
                     ("occurrences_written", tot)):
            fh.write(f"{k}\t{v}\n")
        for name in QUERIES:
            fh.write(f"bytes.{name}\t{(RAW / name).stat().st_size}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true", help="skip the downloads")
    ap.add_argument("--min-species", type=int, default=10,
                    help="species a family needs to be written out (default 10)")
    args = ap.parse_args()

    if not args.build:
        RAW.mkdir(exist_ok=True)
        print("downloading:")
        for name, url in QUERIES.items():
            download(name, url)
    missing = [n for n in QUERIES if not (RAW / n).exists()]
    if missing:
        raise SystemExit(f"missing {', '.join(missing)}, run without --build")
    build(args.min_species)
    return 0


if __name__ == "__main__":
    sys.exit(main())
