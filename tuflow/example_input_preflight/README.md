# TUFLOW input preflight reproduction dataset

This reusable regression fixture comes from the supplied TUFLOW Example Model Dataset.
It is stored in the dedicated test-data repository and consumed by
`ryan-tools/tests/test_data/tuflow/example_input_preflight`, via the existing
`tests/test_data` Git submodule.

## Files

- `examples.zip` — input tree with 1,464 original files (15,137,122 compressed bytes).
- `manifest.json` — relative paths, sizes and SHA-256 checksums for all archive members.
- `baseline.csv` — the original 161-TCF / 174-run diagnostic baseline.

ZIP SHA-256:

`e374c8e072679fc6c4dc11e63b270caa1101b6aebb84d70060872cdd1b0aa7d6`

The archive retains model, runs, BC and pit databases, original input bytes,
geospatial files and the one restart file needed as an input. It excludes
executables, generated simulations, logs and output caches.

## Storage and performance policy

Keep the inputs **compressed in Git**. The extracted tree is about 19.2 MB
spread across 1,464 small files. Committing those separately would increase
Git metadata, clone/checkout work and filesystem operations, particularly
on Windows network drives. Tests should checksum-verify, extract into a
unique local temporary directory **once per test session**, then run all
selected TCFs against that extracted tree. Never decompress on each simulated
context or file check.

To benchmark eager versus deferred PyTUFLOW, perform archive verification and
extraction before starting either timer. Warm-cache comparisons must use the
same extracted directory and full materialised dependency identities.

The test runner lives in ryan-tools:
`tests/fixtures/tuflow_example_repro/run_checks.py`. Example:

```powershell
python -m tests.fixtures.tuflow_example_repro.run_checks --verify-only
python -m tests.fixtures.tuflow_example_repro.run_checks --tcf EG02_014.tcf
```

The fixture tests file/dependency completeness, not hydraulic simulation accuracy.
Do not execute TUFLOW model batches during these diagnostic tests.

The fixture data persists here. Any temporary runner and CI replay may be
removed from ryan-tools PR #143 when the regression workflow is finalised.
