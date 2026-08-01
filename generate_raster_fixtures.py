"""Generate deterministic, synthetic raster fixtures for ryan-tools.

Run this file from any working directory. Generated files are written below
``raster/`` beside this script. The data are deliberately small, synthetic,
and safe to redistribute.
"""

# Rasterio and Fiona do not currently publish enough typing information for
# strict Pyright to understand their dataset and CRS objects.
# pyright: reportMissingTypeStubs=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportAttributeAccessIssue=false

from __future__ import annotations

from collections.abc import Iterable
import json
from pathlib import Path
import shutil

import fiona
import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.transform import Affine, from_origin

OUTPUT_ROOT = Path(__file__).resolve().parent / "raster"
CRS_VALUE = CRS.from_epsg(7850)  # GDA2020 / MGA zone 50
NODATA = -9999.0
ORIGIN_X = 400_000.0
ORIGIN_Y = 6_500_000.0


def _write_tif(path: Path, data: np.ndarray, transform: Affine, *, nodata: float | None = NODATA) -> None:
    """Write one or more Float32 bands as a small TUFLOW-compatible GeoTIFF."""
    bands = data[np.newaxis, ...] if data.ndim == 2 else data
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=bands.shape[2],
        height=bands.shape[1],
        count=bands.shape[0],
        dtype="float32",
        crs=CRS_VALUE,
        transform=transform,
        nodata=nodata,
        compress="DEFLATE",
        predictor=2,
        tiled=True,
        blockxsize=16,
        blockysize=16,
        bigtiff="IF_SAFER",
    ) as dataset:
        dataset.write(bands.astype(np.float32, copy=False))
        dataset.update_tags(fixture="ryan-tools synthetic raster data")


def _base_surface(size: int = 64) -> np.ndarray:
    """Return a sloping surface with a square and an isolated NoData region."""
    rows, columns = np.indices((size, size), dtype=np.float32)
    values = 10.0 + columns * 0.25 + rows * 0.5
    values[8:16, 8:16] = NODATA
    values[48, 48] = NODATA
    return values


def _write_conversion_sources() -> None:
    """Create equivalent ASC, FLT, and XYZ inputs for conversion wrappers."""
    directory = OUTPUT_ROOT / "conversion"
    directory.mkdir(parents=True, exist_ok=True)
    values = _base_surface()
    transform = from_origin(ORIGIN_X, ORIGIN_Y, 2.0, 2.0)

    for driver, suffix in (("AAIGrid", ".asc"), ("EHdr", ".flt")):
        with rasterio.open(
            directory / f"surface{suffix}",
            "w",
            driver=driver,
            width=values.shape[1],
            height=values.shape[0],
            count=1,
            dtype="float32",
            crs=CRS_VALUE,
            transform=transform,
            nodata=NODATA,
        ) as dataset:
            dataset.write(values, 1)

    xyz_lines: list[str] = []
    for row, column in np.ndindex(values.shape):
        x, y = rasterio.transform.xy(transform, row, column, offset="center")
        xyz_lines.append(f"{x:.1f} {y:.1f} {values[row, column]:.2f}\n")
    (directory / "surface.xyz").write_text("".join(xyz_lines), encoding="ascii", newline="\n")


def _write_merge_tiles() -> None:
    """Create adjacent tiles, overlapping tiles, and a vector selection extent."""
    adjacent = OUTPUT_ROOT / "merge" / "adjacent"
    tile_size = 32
    west = np.full((tile_size, tile_size), 1.0, dtype=np.float32)
    east = np.full((tile_size, tile_size), 2.0, dtype=np.float32)
    west[:4, :4] = NODATA
    _write_tif(adjacent / "tile_west.tif", west, from_origin(ORIGIN_X, ORIGIN_Y, 2.0, 2.0))
    _write_tif(
        adjacent / "tile_east.tif",
        east,
        from_origin(ORIGIN_X + 64.0, ORIGIN_Y, 2.0, 2.0),
    )

    overlap = OUTPUT_ROOT / "merge" / "overlap"
    _write_tif(
        overlap / "tile_low.tif",
        np.full((32, 32), 10.0, dtype=np.float32),
        from_origin(ORIGIN_X, ORIGIN_Y, 2.0, 2.0),
    )
    _write_tif(
        overlap / "tile_high.tif",
        np.full((32, 32), 20.0, dtype=np.float32),
        from_origin(ORIGIN_X + 32.0, ORIGIN_Y - 32.0, 2.0, 2.0),
    )

    extent_path = OUTPUT_ROOT / "merge" / "select_west.gpkg"
    extent_path.unlink(missing_ok=True)
    schema = {"geometry": "Polygon", "properties": {"name": "str"}}
    coordinates = [
        [
            (ORIGIN_X + 4.0, ORIGIN_Y - 4.0),
            (ORIGIN_X + 60.0, ORIGIN_Y - 4.0),
            (ORIGIN_X + 60.0, ORIGIN_Y - 60.0),
            (ORIGIN_X + 4.0, ORIGIN_Y - 60.0),
            (ORIGIN_X + 4.0, ORIGIN_Y - 4.0),
        ]
    ]
    with fiona.open(extent_path, "w", driver="GPKG", crs=CRS_VALUE.to_wkt(), schema=schema) as collection:
        collection.write(
            {
                "geometry": {"type": "Polygon", "coordinates": coordinates},
                "properties": {"name": "west"},
            }
        )


def _write_grouped_mosaic_inputs() -> None:
    """Create names consumed by build_VRT.py's default grouping rule."""
    directory = OUTPUT_ROOT / "grouped_mosaic"
    for tile, x, value in (("X143", ORIGIN_X, 1.0), ("X144", ORIGIN_X + 32.0, 2.0)):
        _write_tif(
            directory / f"01_{tile}_DEV_d_HR_Max.tif",
            np.full((16, 16), value, dtype=np.float32),
            from_origin(x, ORIGIN_Y, 2.0, 2.0),
        )


def _write_maintenance_inputs() -> None:
    """Create nodata, flood-depth, multiband, and non-square-cell rasters."""
    directory = OUTPUT_ROOT / "maintenance"
    surface = _base_surface()
    _write_tif(
        directory / "nodata_regions.tif",
        surface,
        from_origin(ORIGIN_X, ORIGIN_Y, 2.0, 2.0),
    )

    depth = np.zeros((64, 64), dtype=np.float32)
    depth[8:40, 8:40] = 0.10
    depth[18:30, 18:30] = 0.50
    depth[50, 50] = 0.50  # isolated pixel for sieve tests
    depth[:4, :] = NODATA
    _write_tif(
        directory / "Synthetic_EXG_01p_060m_TP01_d_HR_Max.tif",
        depth,
        from_origin(ORIGIN_X, ORIGIN_Y, 2.0, 2.0),
    )

    bands = np.stack(
        (
            np.full((32, 32), 1.0, dtype=np.float32),
            np.full((32, 32), 2.0, dtype=np.float32),
            np.full((32, 32), 3.0, dtype=np.float32),
            np.where(np.indices((32, 32))[0] < 16, 0.0, 0.2).astype(np.float32),
        )
    )
    _write_tif(
        directory / "four_band_depth.tif",
        bands,
        from_origin(ORIGIN_X, ORIGIN_Y, 2.0, 2.0),
    )

    non_square = np.arange(96, dtype=np.float32).reshape(8, 12)
    non_square[0, 0] = NODATA
    _write_tif(
        OUTPUT_ROOT / "square_cells" / "non_square_cells.tif",
        non_square,
        from_origin(ORIGIN_X, ORIGIN_Y, 2.0, 3.0),
    )


def _write_velocity_inputs() -> None:
    """Create a coarse velocity grid and a finer depth grid for alignment tests."""
    directory = OUTPUT_ROOT / "velocity_masker"
    velocity = np.arange(1, 65, dtype=np.float32).reshape(8, 8) / 10.0
    velocity[0, 0] = NODATA
    depth = np.zeros((16, 16), dtype=np.float32)
    depth[2:8, 2:8] = 0.04
    depth[5:13, 5:13] = 0.10
    depth[14:, 14:] = NODATA
    _write_tif(
        directory / "Synthetic_EXG_01p_060m_TP01_V_Max.tif",
        velocity,
        from_origin(ORIGIN_X, ORIGIN_Y, 4.0, 4.0),
    )
    _write_tif(
        directory / "Synthetic_EXG_01p_060m_TP01_d_HR_Max.tif",
        depth,
        from_origin(ORIGIN_X, ORIGIN_Y, 2.0, 2.0),
    )


def _ensemble_value(scenario_index: int, result_index: int, duration_index: int, tp: int) -> float:
    return scenario_index * 100.0 + result_index * 10.0 + duration_index * 20.0 + float(tp)


def _write_tuflow_statistics() -> dict[str, dict[str, dict[str, float]]]:
    """Create varied layouts and separator styles for configurable searches."""
    expected: dict[str, dict[str, dict[str, float]]] = {}
    transform = from_origin(ORIGIN_X, ORIGIN_Y, 2.0, 2.0)
    spatial = np.arange(16, dtype=np.float32).reshape(4, 4) / 100.0
    result_types = ("d_HR_Max", "h_HR_Max", "V_Max")
    for scenario_index, scenario in enumerate(("EXG", "DEV")):
        separator = "_" if scenario == "EXG" else "+"
        ensemble_grid_directory = (
            OUTPUT_ROOT / "tuflow_statistics" / "mean_then_max" / "layout_alpha" / "results" / "grids"
            if scenario == "EXG"
            else OUTPUT_ROOT
            / "tuflow_statistics"
            / "mean_then_max"
            / "layout_beta"
            / "nested"
            / "model_outputs"
            / "grids"
        )
        for result_index, result_type in enumerate(result_types):
            key = f"{scenario}/{result_type}"
            expected[key] = {}
            duration_means: list[float] = []
            for duration_index, duration in enumerate(("00030m", "00060m")):
                values: list[float] = []
                for tp in range(1, 11):
                    base_value = _ensemble_value(scenario_index, result_index, duration_index, tp)
                    values.append(base_value)
                    prefix_parts = (
                        "Synthetic",
                        "05",
                        "modelA",
                        scenario,
                        "01.00p",
                        duration,
                        "Ensemble",
                        f"TP{tp:02d}",
                        "08M",
                    )
                    filename = f"{separator.join(prefix_parts)}_{result_type}.tif"
                    _write_tif(
                        ensemble_grid_directory / filename,
                        spatial + base_value,
                        transform,
                    )
                mean_value = float(np.mean(values))
                duration_means.append(mean_value)
                expected[key][duration] = {
                    "cell_0_0_mean": mean_value,
                    "cell_3_3_mean": mean_value + 0.15,
                }

                pmf_value = scenario_index * 100.0 + result_index * 10.0 + duration_index + 1.0
                pmf_prefix_parts = (
                    "Synthetic",
                    "modelB",
                    scenario,
                    "PMP",
                    duration,
                    "PMF",
                    "Dummy",
                    "08M",
                )
                pmf_filename = f"{separator.join(pmf_prefix_parts)}_{result_type}.tif"
                _write_tif(
                    OUTPUT_ROOT / "tuflow_statistics" / "max_search" / scenario / "PMP" / "grids" / pmf_filename,
                    spatial + pmf_value,
                    transform,
                )
            expected[key]["maximum_of_duration_means"] = {
                "cell_0_0": max(duration_means),
                "cell_3_3": max(duration_means) + 0.15,
            }
    return expected


def _write_separator_cases() -> None:
    """Create equivalent underscore and plus names for parser regression tests."""
    directory = OUTPUT_ROOT / "tuflow_statistics" / "separator_cases"
    values = np.arange(16, dtype=np.float32).reshape(4, 4) / 10.0
    transform = from_origin(ORIGIN_X, ORIGIN_Y, 2.0, 2.0)
    parts = ("Synthetic", "modelC", "EXG", "01.00p", "00030m", "TP01", "08M")
    for separator, label in (("_", "underscore"), ("+", "plus")):
        _write_tif(
            directory / label / f"{separator.join(parts)}_d_HR_Max.tif",
            values,
            transform,
        )


def _relative_files(paths: Iterable[Path]) -> list[str]:
    return sorted(path.relative_to(OUTPUT_ROOT).as_posix() for path in paths if path.is_file())


def _validate_fixtures() -> int:
    """Verify that generated rasters reopen with their intended core metadata."""
    tif_paths = sorted(OUTPUT_ROOT.rglob("*.tif"))
    for path in tif_paths:
        with rasterio.open(path) as dataset:
            if dataset.crs != CRS_VALUE:
                raise RuntimeError(f"Unexpected CRS in {path}: {dataset.crs}")
            if any(dtype != "float32" for dtype in dataset.dtypes):
                raise RuntimeError(f"Unexpected dtype in {path}: {dataset.dtypes}")
            if dataset.nodata != NODATA:
                raise RuntimeError(f"Unexpected NoData in {path}: {dataset.nodata}")

    for source_name in ("surface.asc", "surface.flt", "surface.xyz"):
        source_path = OUTPUT_ROOT / "conversion" / source_name
        with rasterio.open(source_path) as dataset:
            if (dataset.height, dataset.width) != (64, 64):
                raise RuntimeError(f"Unexpected dimensions in {source_path}: {dataset.shape}")
    return len(tif_paths)


def main() -> None:
    """Generate all fixtures and a machine-readable expectation manifest."""
    # Refresh only the generated statistics trees, including a superseded first-draft layout.
    for generated_statistics_root in (
        OUTPUT_ROOT / "tuflow_ensemble",
        OUTPUT_ROOT / "tuflow_statistics",
    ):
        if generated_statistics_root.is_dir():
            shutil.rmtree(generated_statistics_root)

    _write_conversion_sources()
    _write_merge_tiles()
    _write_grouped_mosaic_inputs()
    _write_maintenance_inputs()
    _write_velocity_inputs()
    ensemble_expected = _write_tuflow_statistics()
    _write_separator_cases()

    manifest_path = OUTPUT_ROOT / "expected.json"
    generated_files = _relative_files(path for path in OUTPUT_ROOT.rglob("*") if path != manifest_path)
    manifest: dict[str, object] = {
        "crs": "EPSG:7850",
        "nodata": NODATA,
        "origin": [ORIGIN_X, ORIGIN_Y],
        "tuflow_statistics": ensemble_expected,
        "generated_files": generated_files,
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    tif_count = _validate_fixtures()
    print(f"Generated {len(generated_files)} fixture files ({tif_count} GeoTIFFs) " f"under {OUTPUT_ROOT}")


if __name__ == "__main__":
    main()
