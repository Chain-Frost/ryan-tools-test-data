# Synthetic raster fixtures

These small, deterministic fixtures exercise raster utilities in the parent
`ryan-tools` repository. They use GDA2020 / MGA zone 50 (`EPSG:7850`), Float32
pixels, and `-9999` NoData unless a fixture specifically tests another case.

Regenerate them from the test-data repository root with:

```powershell
python generate_raster_fixtures.py
```

The generator overwrites its named outputs, refreshes its own TUFLOW statistics
trees, and does not delete unrelated files.
`expected.json` records the generated inventory and important expected values.

## Fixture groups

- `conversion`: equivalent 64 x 64 ASC, FLT, and XYZ surfaces for conversion,
  GeoTIFF, and overview workflows.
- `merge/adjacent`: two edge-matching tiles; `select_west.gpkg` intersects only
  the western tile. `merge/overlap` supplies two partially overlapping values.
- `grouped_mosaic`: TUFLOW-style tile names for `build_VRT.py` grouping.
- `maintenance`: irregular NoData regions, graduated flood depths, an isolated
  wet pixel for sieve tests, and a four-band raster whose depth is band 4.
- `square_cells`: a raster with 2 m x 3 m pixels.
- `velocity_masker`: a coarse velocity raster and aligned, finer depth raster
  containing values below and above the 0.05 m threshold.
- `tuflow_statistics/max_search`: EXG and DEV grids in the current wrapper's
  editable `<scenario>/PMP/grids` example shape, with two synthetic durations
  and three result types. Use `max_search` as that example's working root.
- `tuflow_statistics/mean_then_max`: the EXG and DEV grids intentionally live
  at different nesting depths below `layout_alpha` and `layout_beta`. Each has
  two durations, three result types, and TP01-TP10; recursive discovery should
  find both from `mean_then_max`.
- `tuflow_statistics/separator_cases`: equivalent `_` and `+` names for parser
  and filename-rewriting regression tests.

The statistics names deliberately use underscore separators for EXG and plus
separators for DEV. Folder names and filename prefixes are examples, not a
fixed schema; tests should exercise editable globs and parser-recognised tokens.
The project names and every cell value are invented.

Tests for scripts that modify inputs, especially `velocity_masker.py` and the
NoData utilities, should copy the fixture to a temporary directory first.
