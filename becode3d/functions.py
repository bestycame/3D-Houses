from pyproj import Transformer
import rasterio
from rasterio.mask import mask
from shapely.geometry import box
import geopandas as gpd
import requests
import json
import os
from becode3d.variables import DATAS
from os.path import join, dirname
from dotenv import load_dotenv

env_path = join(dirname(dirname(__file__)), ".env")
load_dotenv(dotenv_path=env_path)


class ErrorRaised(Exception):
    pass


def lambert_to_wgs(x_lambert: float, y_lambert: float) -> (float, float):
    """
    This function transforms geographic coordinates from Lambert 1972 to WGS84.
    """
    transformer = Transformer.from_crs("epsg:31370", "epsg:4326")
    x_wgs, y_wgs = transformer.transform(x_lambert, y_lambert)
    return x_wgs, y_wgs


def wgs_to_lambert(x_wgs: float, y_wgs: float) -> (float, float):
    """
    This function transforms geographic coordinates from WGS84 to Lambert 1972.
    """
    transformer = Transformer.from_crs("epsg:4326", "epsg:31370")
    x_lambert, y_lambert = transformer.transform(x_wgs, y_wgs)
    return x_lambert, y_lambert


def search_address_mapbox(
    address: str, as_wgs=False, as_dict=False, boundary=100
) -> (float, float, float, float, float, float, dict):
    """
    This function will search the adress in MapBox to return it's coordinates
    and bounding box in the adequate CRS.
    Input: address(str): Address to lookup
           as_wgs(Bool/False): return as L1972 coordinates, or WGS84
           as_dict(Bool/False): returns either a tuple or a dict
           boundary(int/100): controls the size of the bounding box
    Output: x, y: Coordinates of the of the adress found
            xMin, xMax, yMin, yMax(float): bounding box
            address(dict):Details of the address found
    """
    url = "https://api.mapbox.com/geocoding/v5/mapbox.places/{address}.json?types=address&access_token={key}"  # noqa
    r = requests.get(url.format(address=address, key=os.environ["MAPBOX_KEY"]))
    if r.status_code != 200:
        raise ErrorRaised("Incorrect reply from Mapbox API")
    r = r.json()
    if len(r["features"]) == 0:
        raise ErrorRaised("Address not found")
    address = {
        "street": r["features"][0]["text"],
        "postal_code": r["features"][0]["context"][0]["text"],
        "city_name": r["features"][0]["context"][1]["text"],
    }
    y, x = r["features"][0]["center"]
    # Lambert are easier to add a metered value to the coordinates
    x, y = wgs_to_lambert(x, y)
    xMin, xMax = x - boundary, x + boundary
    yMin, yMax = y - boundary, y + boundary
    # transforms to the correct CRS if required
    if as_wgs:
        x, y = lambert_to_wgs(x, y)
        xMin, xMax = lambert_to_wgs(xMin, xMax)
        yMin, yMax = lambert_to_wgs(yMin, yMax)
    # returns the data as a dict instead of a tuple
    if as_dict:
        return {
            "x": x,
            "xMin": xMin,
            "xMax": xMax,
            "y": y,
            "yMin": yMin,
            "yMax": yMax,
            "address": address,
        }
    return x, y, xMin, xMax, yMin, yMax, address


def is_in_bbox(x, y, bbox):
    """
    Answers True or Folse if the x, y is inside the BBOX.
    """
    xMin, yMin, xMax, yMax = bbox
    if xMin <= x <= xMax and yMin <= y <= yMax:
        return True
    return False


def find_files(xMin, xMax, yMin, yMax):
    """
    Will find in wich MNS/MNT file the BBOX is.
    """
    bboxes = {
        key: rasterio.open(next(iter(DATAS[key].values()))).bounds
        for key in DATAS.keys()
    }
    for k, bbox in bboxes.items():
        if is_in_bbox(xMin, yMin, bbox) and is_in_bbox(xMax, yMax, bbox):
            return DATAS[k]
    raise ErrorRaised("boundary not found in TIFF file.")


def getFeatures(gdf):
    """
    Function to parse features from GeoDataFrame
    in such a manner that rasterio wants them
    """
    return [json.loads(gdf.to_json())["features"][0]["geometry"]]


def subsetTif(xMin, xMax, yMin, yMax, in_tif):
    """
    Crops a the in_tif on the bounding box and returns an out_tif
    """
    data = rasterio.open(in_tif)
    geo = gpd.GeoDataFrame(
        {"geometry": box(xMin, yMin, xMax, yMax)}, index=[0], crs="EPSG:31370"
    )
    out_tif, _ = mask(
        dataset=data, shapes=getFeatures(geo), filled=False, crop=True
    )
    return out_tif
