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

Before adding or redistributing third-party datasets, confirm their licensing and record their source here.
