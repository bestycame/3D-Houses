from pyproj import Transformer
import rasterio
from rasterio.mask import mask
from shapely.geometry import box
from matplotlib.colors import LightSource
import geopandas as gpd
import requests
import json
import plotly.express as px
import os
from becode3d.variables import DATAS
from os.path import join, dirname
from dotenv import load_dotenv

env_path = join(dirname(dirname(__file__)), '.env')
load_dotenv(dotenv_path=env_path)


class ErrorRaised(Exception):
    pass


def lambert_to_wgs(x_lambert, y_lambert):
    transformer = Transformer.from_crs("epsg:31370", "epsg:4326")
    x_wgs, y_wgs = transformer.transform(x_lambert, y_lambert)
    return x_wgs, y_wgs


def wgs_to_lambert(x_wgs, y_wgs):
    transformer = Transformer.from_crs("epsg:4326", "epsg:31370")
    x_lambert, y_lambert = transformer.transform(x_wgs, y_wgs)
    return x_lambert, y_lambert


def search_address_mapbox(address, as_wgs=False, as_dict=False, boundary=100):
    url = "https://api.mapbox.com/geocoding/v5/mapbox.places/{address}.json?types=address&access_token={key}"
    r = requests.get(url.format(address=address, key=os.environ['MAPBOX_KEY']))
    if r.status_code != 200:
        raise ErrorRaised("Incorrect reply from Mapbox API")
    r = r.json()
    if len(r['features']) == 0:
        raise ErrorRaised("Address not found")
    address = {'street': r['features'][0]['text'],
               'postal_code': r['features'][0]['context'][0]['text'],
               'city_name': r['features'][0]['context'][1]['text']}
    y, x = r['features'][0]['center']
    x, y = wgs_to_lambert(x, y)
    xMin, xMax = x - boundary, x + boundary
    yMin, yMax = y - boundary, y + boundary
    if as_wgs:
        x, y = lambert_to_wgs(x, y)
        xMin, xMax = lambert_to_wgs(xMin, xMax)
        yMin, yMax = lambert_to_wgs(yMin, yMax)
    if as_dict:
        return {'x': x, 'xMin': xMin, 'xMax': xMax,
                'y': y, 'yMin': yMin, 'yMax': yMax,
                'address': address}
    return x, y, xMin, xMax, yMin, yMax, address


def is_in_bbox(x, y, bbox):
    xMin, yMin, xMax, yMax = bbox
    if xMin <= x <= xMax and yMin <= y <= yMax:
        return True
    return False


def find_files(xMin, xMax, yMin, yMax):
    bboxes = {key: rasterio.open(next(iter(DATAS[key].values()))).bounds for key in DATAS.keys()}
    for k, bbox in bboxes.items():
        if is_in_bbox(xMin, yMin, bbox) and is_in_bbox(xMax, yMax, bbox):
            return DATAS[k]
    raise ErrorRaised("boundary not found in TIFF file.")


def getFeatures(gdf):
    """Function to parse features from GeoDataFrame in such a manner that rasterio wants them"""
    return [json.loads(gdf.to_json())['features'][0]['geometry']]


def subsetTif(xMin, xMax, yMin, yMax, in_tif):
    data = rasterio.open(in_tif)
    geo = gpd.GeoDataFrame({'geometry': box(xMin, yMin, xMax, yMax)}, index=[0], crs="EPSG:31370")
    out_img, _ = mask(dataset=data, shapes=getFeatures(geo), filled=False, crop=True)
    return out_img


def show_tif(tif, title=None, hillshade=False):
    if title is None:
        title = tif
    colors = [[0.0, 'rgb(000, 063, 076)'], [0.1, 'rgb(029, 081, 059)'], [0.2, 'rgb(055, 098, 043)'],
              [0.3, 'rgb(079, 114, 030)'], [0.4, 'rgb(103, 129, 016)'], [0.5, 'rgb(136, 142, 002)'],
              [0.6, 'rgb(169, 154, 021)'], [0.7, 'rgb(192, 171, 045)'], [0.8, 'rgb(214, 188, 074)'],
              [0.9, 'rgb(234, 209, 112)'], [1.0, 'rgb(254, 229, 152)']]

    with rasterio.open(tif) as src:
        data = src.read(1)

    if hillshade:
        light = LightSource(azdeg=315, altdeg=45)
        data = light.hillshade(data, vert_exag=1)

    fig = px.imshow(data, color_continuous_scale=colors)
    fig.update_traces(customdata=data, hovertemplate='elevation: %{customdata:.4f}')
    fig.update_layout(**dict(title_text=title, width=700, height=500, template='none'))
    return fig
