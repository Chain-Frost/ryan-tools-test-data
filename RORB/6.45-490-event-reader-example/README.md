# Original RORBWin 6.45 reader fixtures

Owner-authorised public inputs/outputs, prepared 16 November 2026 for
[ryan-tools PR #233](https://github.com/Chain-Frost/ryan-tools/pull/233) and
[python-runoff-routing #142](https://github.com/Chain-Frost/python-runoff-routing/issues/142).
This is a complete **490-event** archived batch, not the unlocated historical
420-pair dataset. It provides an authentic, separately identified 6.45 acceptance
population; it does not prove that the historic 420-pair recheck occurred.

## Contents and provenance

- `RORB_14141_batch.out`: 490 event rows, reporting program version 6.45
  (last updated 20 March 2019), run date 13 July 2022 14:14.
- 490 matching `.csv` hydrographs and 490 individual `.out` reports.
- 491 available `.stm` inputs, including the base storm.
- `manifest.json`: original SHA-256/size, distributed SHA-256/size and exact
  directory-replacement counts for all 1,472 input/output files.
- `validation.json`: current-reader revision, environment, all 490 composite
  event identities and individual association outcomes.

The retained archive source is RF/CT820. The executable hash/build and the
identity of the previously reported 420-pair population are unknown. The banner
is evidence of the reported version, not executable authentication. The CATG
referenced by the reports was not present in this source directory; this fixture
is for reading existing reports, not for rerunning the numerical model.

The only transformation replaces absolute Windows directory prefixes through
the final backslash with `.\`. Basenames, embedded spaces, all numeric tokens,
event order, original clocks, precision and line endings remain unchanged.
Every line without such a prefix was checked byte-for-byte. Files are marked
`-text` in the repository's `.gitattributes` to prevent checkout conversion.
No executable, manual, trace or generated numerical result is included.

## Reader validation and reuse

Windows / Python 3.14.6, exact PR233 reader revision
`598e5edea093df426cda64c3a528fd1c5784c612`:
**490/490 corroborated, zero missing/ambiguous/mismatch**, both in-place originals
and distributed path-sanitised fixtures. All 1,472 distributed file hashes and
sizes verified. This was a read-only parser check; no native executable ran.

Clone this repository and check out the immutable data commit linked in the
PR233 handoff (a branch archive works too). Verify `manifest.json` before use.
Use the canonical reader already provided by PR233 or downstream PR165; do not
copy report grammar. With that reader installed, run from the data checkout:

```python
from collections import Counter
from pathlib import Path

from ryan_library.functions.RORB import readers
from ryan_library.functions.RORB.associations import associate_batch_csvs

root = Path("RORB/6.45-490-event-reader-example")
print(readers.__file__)  # Verify the intended pinned reader installation.
batch = readers.read_rorb_file(root / "RORB_14141_batch.out")
assert batch.kind == "batch_output"
assert batch.section("runs").valid
assert len(batch.section("runs").rows) == 490
associations = associate_batch_csvs(batch, max_runs=500)
counts = Counter(str(row["status"]) for row in associations.rows)
assert associations.valid and counts == {"corroborated": 490}, counts
print(counts)
```

Do not force `EXPECTED_RUNS = 420` onto this dataset or claim it is the old
420-pair source. The receiving agent should record this alternative population
and explicitly reconcile the earlier acceptance wording in PR233/#142.

## Limits

The batch site description is blank; preserve that source fact. Association
corroborates the reported role/label and printed peak, not a physical site ID.
The first event has 501 hydrograph rows: its `.out`/CSV comparison preserves
matching flows and a reported CSV-minus-output **+0.5 hour** offset, returning
`mismatch` for the different clocks. This is separate from the historical
420-pair handoff's reported +1 hour offset. Never shift either time axis.

Reader association does not qualify generated effective inputs, numerical
equivalence, native representative-event rules or critical-duration selection.
No selection implementation, merge or release is authorised by this receipt.
