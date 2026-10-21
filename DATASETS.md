# Dataset inventory and provenance

## TUFLOW data

The `tuflow` directory contains example-model, tutorial, log, result, and regression inputs used by the
`ryan-tools` test suite.

The repository was extracted from the complete `tests/test_data` history of
[`Chain-Frost/ryan-tools`](https://github.com/Chain-Frost/ryan-tools) on 18 July 2026. Paths were moved from
`tests/test_data/...` to the repository root while preserving Git authorship, timestamps, commit messages, and
file evolution.

The extraction deliberately excluded every XLSX path from all refs. The source tip and extracted tip were
compared byte-for-byte before publication: 7,432 files and 147,063,632 bytes matched.

The archived [TUFLOW input preflight examples](tuflow/example_input_preflight/README.md)
were assembled from the user-supplied TUFLOW Example Model Dataset for
read-only eager/deferred dependency regression tests. The archive contains
1,464 original input members, a manifest of member hashes, and an initial
161-TCF / 174-run diagnostic baseline. Only source model inputs and one
required restart input were retained; no executables, simulation outputs
or generated caches are redistributed.

Before adding or redistributing third-party datasets, confirm their licensing and record their source here.

## Synthetic raster data

The `raster` directory is generated locally by `generate_raster_fixtures.py`.
It contains no third-party source data: all pixel values, names, transforms,
and vector geometry are deterministic synthetic examples created for testing
the raster utilities in `ryan-tools`.
