"""One-shot correction of missing CRS declarations in three disposable tutorial inputs.

Do not change samples, geometry, raster transforms or unrelated ZIP members.
The source archive is the only authored copy of the original example inputs.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

import netCDF4
import numpy as np
import rasterio
from pyproj import CRS

HERE = Path(__file__).resolve().parents[1] / "tuflow/example_input_preflight"
ARCHIVE = HERE / "examples.zip"
MANIFEST = HERE / "manifest.json"
README = HERE / "README.md"
NETCDF = "bc_dbase/EG03_011_rf.nc"
TIFF = "model/grid/EG06_2D_002_IWL_h.tif"
SHAPE = "model/gis/1d_mh_EG15_006_P.shp"
PRJ = "model/gis/1d_mh_EG15_006_P.prj"
EXPECTED_SOURCE_COUNT = 1464
CRS = CRS.from_epsg(32760)


def hash_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def actual_raster_crs(path: Path) -> CRS | None:
    # Replicate the PyTuflow validation environment: raster PAM sidecars disabled.
    with rasterio.Env(GDAL_PAM_ENABLED="NO"):
        with rasterio.open(path) as root:
            if root.count and root.width and root.height:
                return CRS.from_user_input(root.crs) if root.crs else None
            for name in root.subdatasets:
                with rasterio.open(name) as variable:
                    if variable.count and variable.width and variable.height:
                        return CRS.from_user_input(variable.crs) if variable.crs else None
    raise ValueError(f"No usable raster bands: {path}")


def set_netcdf_crs(path: Path) -> None:
    # CF grid_mapping + spatial_ref defines the coordinate system for GDAL/NetCDF.
    # Only metadata is appended; existing data variables and their values are unchanged.
    with netCDF4.Dataset(path, "r+") as dataset:
        before = {
            name: hash_bytes(np.asarray(var[:]).tobytes())
            for name, var in dataset.variables.items()
            if len(var.dimensions) >= 2 and np.issubdtype(var.dtype, np.number)
        }
        if not before:
            raise ValueError("No numeric gridded NetCDF variable found")
        name = "tutorial_crs"
        if name in dataset.variables:
            raise ValueError("Unexpected pre-existing tutorial CRS variable")
        entry = dataset.createVariable(name, "i4", ())
        wkt = CRS.to_wkt(version="WKT1_GDAL")
        entry.spatial_ref = wkt
        entry.crs_wkt = wkt
        entry.grid_mapping_name = "transverse_mercator"
        entry.longitude_of_central_meridian = 177.0
        entry.latitude_of_projection_origin = 0.0
        entry.scale_factor_at_central_meridian = 0.9996
        entry.false_easting = 500000.0
        entry.false_northing = 10000000.0
        for variable_name in before:
            dataset.variables[variable_name].setncattr("grid_mapping", name)
        dataset.sync()
        after = {
            variable_name: hash_bytes(np.asarray(dataset.variables[variable_name][:]).tobytes())
            for variable_name in before
        }
        assert before == after, "NetCDF numerical array changed"


def set_geotiff_crs(path: Path) -> None:
    with rasterio.open(path, "r+") as dataset:
        arrays_before = tuple(hash_bytes(dataset.read(band).tobytes()) for band in dataset.indexes)
        transform_before = dataset.transform
        dataset.crs = CRS
    with rasterio.open(path) as dataset:
        arrays_after = tuple(hash_bytes(dataset.read(band).tobytes()) for band in dataset.indexes)
        assert arrays_before == arrays_after, "GeoTIFF pixel data changed"
        assert dataset.transform == transform_before, "GeoTIFF transform changed"


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    original_sha = hash_bytes(ARCHIVE.read_bytes())
    assert manifest["archive_sha256"] == original_sha
    original_size = ARCHIVE.stat().st_size
    listing = {row["path"]: row for row in manifest["files"]}
    assert len(listing) == EXPECTED_SOURCE_COUNT
    assert PRJ not in listing
    assert all(name in listing for name in (NETCDF, TIFF, SHAPE))
    projection = CRS.to_wkt(version="WKT1_GDAL").encode("utf-8")
    assert CRS.from_wkt(projection.decode()).equals(CRS)

    with TemporaryDirectory(prefix="tutorial-crs-") as temporary:
        directory = Path(temporary)
        changed: dict[str, bytes] = {}
        with ZipFile(ARCHIVE) as source:
            members = source.infolist()
            assert len(members) == len(listing) == EXPECTED_SOURCE_COUNT
            assert {member.filename for member in members} == set(listing)
            for name in (NETCDF, TIFF):
                destination = directory / Path(name).name
                content = source.read(name)
                assert hash_bytes(content) == listing[name]["sha256"]
                destination.write_bytes(content)
                assert actual_raster_crs(destination) is None, name
                if name == NETCDF:
                    set_netcdf_crs(destination)
                else:
                    set_geotiff_crs(destination)
                assert actual_raster_crs(destination) is not None, name
                assert actual_raster_crs(destination).equals(CRS), name
                changed[name] = destination.read_bytes()
                listing[name]["size"] = len(changed[name])
                listing[name]["sha256"] = hash_bytes(changed[name])
            patched = directory / "patched.zip"
            with ZipFile(patched, "w", compression=ZIP_DEFLATED) as target:
                for member in members:
                    target.writestr(member, changed.get(member.filename, source.read(member.filename)))
                target.writestr(PRJ, projection)
            with ZipFile(patched) as target:
                assert len(target.namelist()) == EXPECTED_SOURCE_COUNT + 1
                for member in target.infolist():
                    data = target.read(member.filename)
                    expected = listing.get(member.filename)
                    if expected is not None:
                        assert expected["size"] == len(data)
                        assert expected["sha256"] == hash_bytes(data), member.filename
                assert target.read(PRJ) == projection
            patched.replace(ARCHIVE)

    manifest["files"].append(
        {"path": PRJ, "size": len(projection), "sha256": hash_bytes(projection)}
    )
    updated_sha = hash_bytes(ARCHIVE.read_bytes())
    manifest["archive_sha256"] = updated_sha
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    original = README.read_text(encoding="utf-8")
    updated = (original
        .replace("1,464 original files", "1,465 original files")
        .replace(f"{original_size:,} compressed bytes", f"{ARCHIVE.stat().st_size:,} compressed bytes")
        .replace(original_sha, updated_sha))
    assert updated != original
    assert original_sha not in updated
    assert "1,465 original files" in updated
    README.write_text(updated, encoding="utf-8")
    print("Patched archive:", updated_sha, ARCHIVE.stat().st_size)
    print("Data-only change: NetCDF CRS metadata, GeoTIFF CRS metadata, shapefile .prj")
    print("Unchanged: numerical arrays, GeoTIFF pixel arrays/transform and 1,462 other ZIP members")


if __name__ == "__main__":
    main()
