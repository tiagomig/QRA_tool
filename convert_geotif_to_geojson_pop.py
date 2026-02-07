import rasterio
import rasterio.features
import geopandas
import os
import datetime
from shapely.geometry import box
from pyproj import Transformer
from tqdm import tqdm

def raster_to_pixel_squares(fin, bbox=None, use_intersection=True, define_zero_squares=False):
    print(f"[INFO] Input raster file: {fin}")

    fout = os.path.splitext(fin)[0] + "_pixel_squares_flt.geojson"
    print(f"[INFO] Output GeoJSON file will be: {fout}")

    print("[INFO] Opening raster file...")
    with rasterio.open(fin) as dataset:
        print("[INFO] Reading raster band...")
        band = dataset.read(1)
        rows, cols = band.shape
        print(f"[INFO] Raster dimensions: {rows} rows x {cols} columns ({band.size} pixels).")
        print(f"[INFO] Raster CRS: {dataset.crs}.")
        print(f"[INFO] Pixel size: {dataset.res[0]} x {dataset.res[1]}.")

        raster_crs = dataset.crs
        target_crs = "EPSG:4326"
        transformer = Transformer.from_crs(raster_crs, target_crs, always_xy=True)

        if bbox is not None:
            bbox_geom = box(*bbox)
        else:
            bbox_geom = None

        shapes = []
        nodata = dataset.nodata

        print("[INFO] Extracting square pixels and filtering early...")
        for idx in tqdm(range(rows), desc="Rows", unit="row"):
            for jdx in range(cols):
                v = band[idx, jdx]
                # Skip nodata for population rasters
                if v == nodata or (not define_zero_squares and v == 0):
                    continue
                # Get pixel bounds in raster CRS
                x0, y0 = dataset.xy(idx, jdx)
                x1 = x0 + dataset.res[0]
                y1 = y0 - dataset.res[1]

                # Transform corners to WGS84 (EPSG:4326)
                lon0, lat0 = transformer.transform(x0, y1)
                lon1, lat1 = transformer.transform(x1, y0)

                # Pixel square in WGS84
                pixel_square_4326 = box(min(lon0, lon1), min(lat0, lat1), max(lon0, lon1), max(lat0, lat1))

                # Early bbox filter (in WGS84)
                if bbox_geom is not None:
                    if use_intersection:
                        if not pixel_square_4326.intersects(bbox_geom):
                            continue
                    else:
                        if not pixel_square_4326.centroid.within(bbox_geom):
                            continue

                shapes.append({'geometry': pixel_square_4326, 'population': int(v)})

        print(f"[INFO] Extracted {len(shapes)} features after early filtering.")

        # Create GeoDataFrame once, at the end
        gdf = geopandas.GeoDataFrame(shapes, crs=target_crs)

        print("[INFO] Writing GeoDataFrame to GeoJSON file...")
        gdf.to_file(fout, driver="GeoJSON")
        print(f"[INFO] Saved GeoJSON to {fout}")

def convert_geotif_to_geojson(fin, bbox=None, use_intersection=True):
    print(f"[INFO] Input raster file: {fin}")

    fout = os.path.splitext(fin)[0] + ".geojson"
    print(f"[INFO] Output GeoJSON file will be: {fout}")

    print("[INFO] Opening raster file...")
    with rasterio.open(fin) as dataset:
        print("[INFO] Reading raster band...")
        image = dataset.read(1)
        mask = image != dataset.nodata

        print("[INFO] Extracting shapes from raster...")
        results_gen = rasterio.features.shapes(image, mask=mask, transform=dataset.transform)
        results = (
            {'properties': {'population': v}, 'geometry': s}
            for i, (s, v) in enumerate(tqdm(results_gen, desc="Shapes", unit="shape"))
        )
        geoms = list(results)
        print(f"[INFO] Extracted {len(geoms)} features.")
        print("[INFO] Creating GeoDataFrame...")
        gdf = geopandas.GeoDataFrame.from_features(geoms)
        print("[INFO] Assigning CRS from raster to GeoDataFrame...")
        gdf.set_crs(dataset.crs, inplace=True)
        print("[INFO] Reprojecting GeoDataFrame to EPSG:4326 (WGS84)...")
        gdf = gdf.to_crs("EPSG:4326")

        if bbox is not None:
            print(f"[INFO] Filtering features within bounding box: {bbox}")
            bbox_geom = box(*bbox)
            if use_intersection:
                filtered = gdf[gdf.intersects(bbox_geom)]
                print(f"[INFO] {len(filtered)} features intersect the bounding box.")
            else:
                filtered = gdf[gdf.centroid.within(bbox_geom)]
                print(f"[INFO] {len(filtered)} features with centroid inside the bounding box.")
            gdf = filtered

        print("[INFO] Writing GeoDataFrame to GeoJSON file...")
        gdf.to_file(fout, driver='GeoJSON')
        print(f"[INFO] Saved GeoJSON to {fout}")

#==========================
# MAIN
start_time = datetime.datetime.now()
print(f"[INFO] Processing started at: {start_time}")

f_in = './data/GHS_POP_E2025_GLOBE_R2023A_54009_100_V1_0_R6_C17.tif'

bbox = (-14.60, 28.01, -13.72, 28.78) # Fuerteventura with margin

use_intersection = True

define_zero_squares = False

# convert_geotif_to_geojson(f_in, bbox=bbox, use_intersection=use_intersection)
raster_to_pixel_squares(f_in, bbox=bbox, use_intersection=use_intersection, define_zero_squares=define_zero_squares)

end_time = datetime.datetime.now()
elapsed_time = end_time - start_time
print(f"[INFO] Processing finished at: {end_time}")
print(f"Temps écoulé : {elapsed_time}")
