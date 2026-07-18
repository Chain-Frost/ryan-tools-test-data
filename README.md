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

The Python tests remain in `ryan-tools`. Running them without this repository populated at
`tests/test_data` is unsupported and fails during pytest startup.

Historical branches under `archive/` preserve test-data changes that were not reachable from the source
repository's `main` branch. XLSX files were intentionally removed from all history during extraction.
