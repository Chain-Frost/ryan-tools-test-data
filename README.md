# ryan-tools test data

This repository contains the large test datasets used by
[`Chain-Frost/ryan-tools`](https://github.com/Chain-Frost/ryan-tools).

It is consumed as a Git submodule at the only supported location:

```text
ryan-tools/tests/test_data
```

Clone the main repository and initialise all submodules with:

```bash
git clone --recurse-submodules https://github.com/Chain-Frost/ryan-tools.git
```

For an existing clone:

```bash
git submodule update --init --recursive
```

## Updating test data

Git normally checks out submodules at a detached commit. Before changing test
data, enter this repository, switch to its tracked `main` branch, and update it:

```bash
cd tests/test_data
git switch main
git pull --ff-only
```

After adding or changing test data, commit and push it from this repository:

```bash
git add .
git commit -m "Update test data"
git push
```

The parent `ryan-tools` repository must then record the new submodule commit:

```bash
cd ../..
git add tests/test_data
git commit -m "Update test-data submodule"
git push
```

If `git submodule update` detaches the test-data checkout again later, run
`git switch main` before making the next update.

The Python tests remain in `ryan-tools`. Running them without this repository populated at
`tests/test_data` is unsupported and fails during pytest startup.

Small synthetic raster fixtures used by the GDAL, raster, and TUFLOW utilities
live under [`raster`](raster/README.md). Regenerate them with
`python generate_raster_fixtures.py`.

Historical branches under `archive/` preserve test-data changes that were not reachable from the source
repository's `main` branch. XLSX files were intentionally removed from all history during extraction.
