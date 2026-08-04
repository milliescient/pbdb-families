# PBDB families

Every family in the Paleobiology Database with a species-level fossil record, written as the
taxon tables `readTaxonData` reads. Built for asking what a fossilized birth-death range
model can estimate from one clade, and what only a pool of clades can.

Nothing downloaded or derived is tracked. `fetch.py` brings all of it back:

    python3 fetch.py                     # download, then build every family
    python3 fetch.py --build             # rebuild from raw/ without downloading
    python3 fetch.py --min-species 20    # only the families big enough to fit alone

Every family with a species-level record gets a table, all 9167 of them, down to the ones
with a single species. Which families are worth fitting is a question for the analysis, and
`index.tsv` carries the counts to answer it, so putting a floor in the extraction would
decide it too early and invisibly.

## What it fetches

Three bulk queries against `paleobiodb.org/data1.2`, unauthenticated, into `raw/`:

  families.tsv      every family, with PBDB's own occurrence and subtaxon counts
  occurrences.tsv   every occurrence identified to species, carrying its family
  extant.tsv        the extant species, which is what makes a status extant

Three queries rather than one per family. PBDB streams a whole result set far more cheaply
than it answers fifteen thousand small questions, and the grouping is local work anyway.

## What it builds

`taxa/<Family>.tsv`, one row per occurrence:

    taxon	min_age	max_age	status

Ages are the occurrence bounds in Ma, unshifted, so a truncation offset is the analysis's
choice rather than baked into the data. A species is placed in its family by the occurrence
record's own classification, so a taxon PBDB knows about but has never recorded an
occurrence for does not appear anywhere here. `status` is `extant` for a species on PBDB's
extant list and `extinct` otherwise, which is a claim about the species rather than an
inference from its youngest occurrence reaching the present.

`index.tsv` lists every family written, with its species, occurrence and extant-species
counts, and is the fastest way to pick a size class to work on. The distribution is steep:
687 families carry 50 or more species, 1064 carry 20 to 49, 1221 carry 10 to 19, and 4613
carry four or fewer.

Of PBDB's 15177 families, 11711 have an occurrence of some kind and 9167 have one
identified to species. The rest are recorded only to genus or coarser, so they cannot
produce a species-level table and do not appear here.

## Two things to know before using this

PBDB is edited continuously, so a fetch is dated rather than fixed. `manifest.tsv` records
when this copy was taken and how much came back. Two runs weeks apart will not agree
exactly, and that is the database improving, not a bug here.

The occurrence bounds are interval bounds, not dated horizons. A great many are the whole
stage, so a species known from one collection carries the stage's width as its uncertainty.
That is the quantity the range model treats as an occurrence age range, and it is why the
per-family record is thin in a way the raw occurrence count hides.
