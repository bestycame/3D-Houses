import rasterio
from rasterio.features import shapes
from rasterio.plot import show
from rasterio.plot import show_hist
from rasterio.mask import mask
from shapely.geometry import box
from fiona.crs import from_epsg
from matplotlib.colors import LightSource
import geopandas as gpd
import requests
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import open3d as o3d
import matplotlib.pyplot as plt
import seaborn as sns
import fiona
import pycrs
import json
import pprint
import plotly.graph_objs as go
import plotly.express as px
from datetime import datetime
province = "HAINAUT"
MNS_MNT = "MNS"
personal_path = "/Volumes/T7/Data"
file_path = f"{personal_path}/RELIEF_WALLONIE_{MNS_MNT}_2013_2014_{province}.tif"
DATAS =  {'LGE' : {'MNT': '/media/bestycame/407C5CD57C5CC776/3D/RELIEF_WALLONIE_MNT_2013_2014_LIEGE.tif',
                   'MNS': '/media/bestycame/407C5CD57C5CC776/3D/RELIEF_WALLONIE_MNS_2013_2014_LIEGE.tif'},
          'HAI' : {'MNT': '/mnt/3D/RELIEF_WALLONIE_MNT_2013_2014_HAINAUT.tif',
                   'MNS': '/mnt/3D/RELIEF_WALLONIE_MNS_2013_2014_HAINAUT.tif'},
          'LUX' : {'MNT': '/mnt/3D/RELIEF_WALLONIE_MNT_2013_2014_LUXEMBOURG.tif',
                   'MNS': '/mnt/3D/RELIEF_WALLONIE_MNS_2013_2014_LUXEMBOURG.tif'},
          'NAM' : {'MNT': '/mnt/3D/RELIEF_WALLONIE_MNT_2013_2014_NAMUR.tif',
                   'MNS': '/mnt/3D/RELIEF_WALLONIE_MNS_2013_2014_NAMUR.tif'},
          'BRA' : {'MNT': '/mnt/3D/RELIEF_WALLONIE_MNT_2013_2014_BRABANT.tif',
                   'MNS': '/mnt/3D/RELIEF_WALLONIE_MNS_2013_2014_BRABANT.tif'}}

from pyproj import Transformer


def lambert_to_wgs(x_lambert, y_lambert):
    transformer = Transformer.from_crs("epsg:31370", "epsg:4326")
    x_wgs, y_wgs = transformer.transform(x_lambert, y_lambert)
    return x_wgs, y_wgs


def wgs_to_lambert(x_wgs, y_wgs):
    transformer = Transformer.from_crs("epsg:4326", "epsg:31370")
    x_lambert, y_lambert = transformer.transform(x_wgs, y_wgs)
    return x_lambert, y_lambert


# x, y, xMin, xMax, yMin, yMax = search_address(cp='5000', rue='RUE DE LA CRETE', num = '111', as_wgs=False)
def search_address(cp, rue, num, as_wgs=False, as_dict=False, boundary=False):
    url = 'http://geoservices.wallonie.be/geolocalisation/rest/getPositionByCpRueAndNumero/{cp}/{rue}/{num}'
    r = requests.get(url.format(cp=cp, rue=rue, num=num)).json()
    x, y, xMin, xMax, yMin, yMax = r['x'], r['y'], r['rue']['xMin'], r['rue']['xMax'], r['rue']['yMin'], r['rue'][
        'yMax']
    if as_wgs:
        x, y = lambert_to_wgs(x, y)
        xMin, xMax = lambert_to_wgs(xMin, xMax)
        yMin, yMax = lambert_to_wgs(yMin, yMax)
    if as_dict:
        return {'x': x, 'xMin': xMin, 'xMax': xMax,
                'y': y, 'yMin': yMin, 'yMax': yMax}
    return x, y, xMin, xMax, yMin, yMax


# x, y, xMin, xMax, yMin, yMax = search_address_mapbox("Rue du roton 38, 6000 Charleroi", as_wgs=False, boundary=150)
def search_address_mapbox(address, as_wgs=False, as_dict=False, boundary=100):
    key = 'pk.eyJ1IjoiYmFjYXlhdzU1OSIsImEiOiJja2dtNTgyNW8wMWN2MnBzM2loNGt4NmlzIn0.3IYulU7qzfpq2Ms0aaYWMQ'
    url = "https://api.mapbox.com/geocoding/v5/mapbox.places/{address}.json?types=address&access_token={key}"
    r = requests.get(url.format(address=address, key=key))
    if r.status_code != 200:
        return 'NotFound'
    r = r.json()
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
                'y': y, 'yMin': yMin, 'yMax': yMax}
    return x, y, xMin, xMax, yMin, yMax


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
    return 'File not found'


def getFeatures(gdf):
    """Function to parse features from GeoDataFrame in such a manner that rasterio wants them"""
    return [json.loads(gdf.to_json())['features'][0]['geometry']]


def subsetTif(xMin, xMax, yMin, yMax, in_tif, out_tif=None):
    if out_tif == None:
        out_tif = datetime.now().strftime('%Y%m%d_%H%M%S.%f') + '.tif'
    data = rasterio.open(in_tif)
    geo = gpd.GeoDataFrame({'geometry': box(xMin, yMin, xMax, yMax)}, index=[0], crs=from_epsg(31370))
    out_img, out_transform = mask(dataset=data, shapes=getFeatures(geo), filled=False, crop=True)
    out_meta = data.meta.copy()
    out_meta.update({"driver": "GTiff",
                     "height": out_img.shape[1],
                     "width": out_img.shape[2],
                     "transform": out_transform,
                     "crs": pycrs.parse.from_epsg_code(31370).to_proj4()
                     })
    with rasterio.open(out_tif, "w", **out_meta) as dest:
        dest.write(out_img)
    return out_tif


# show_tif('subset.tif', title=address, hillshade=False)
def show_tif(tif, title=None, hillshade=False):
    if title == None:
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


def create_chm(xMin, xMax, yMin, yMax):
    files = find_files(xMin, xMax, yMin, yMax)
    time = datetime.now().strftime('%Y%m%d_%H%M%S.%f') + '.tif'
    for k, file in files.items():
        subsetTif(xMin, xMax, yMin, yMax, file, k + '_' + time)
    !gdal_calc.py - A
    MNS_$time - B
    MNT_$time - -outfile = CHM_$time - -calc = "A-B" - -NoDataValue - 9999
    return time

gdb = fiona.open('./BATI3D_2013-2014.gdb', layer=0)
hits = list(gdb.items(bbox=(xMin, yMin, xMax, yMax)))

features = []
for hit in hits:
    features.append({'id':           hit[0],
                        'H_MUR':        hit[1]['properties']['H_MUR'],
                        'H_TOIT':       hit[1]['properties']['H_TOIT'],
                        'E_TOIT':       hit[1]['properties']['E_TOIT'],
                        'Q_LIDAR':      hit[1]['properties']['Q_LIDAR'],
                        'Q_BATI' :      hit[1]['properties']['Q_BATI'],
                        'SHAPE_Length': hit[1]['properties']['SHAPE_Length'],
                        'SHAPE_Area':   hit[1]['properties']['SHAPE_Area'],
                        'X': [int(x[0]) for x in hit[1]['geometry']['coordinates'][0][0]],
                        'Y': [int(x[1]) for x in hit[1]['geometry']['coordinates'][0][0]]
                       })

data = rasterio.open(f'CHM_{time}')
xMin, yMin, xMax, yMax = data.bounds
z_data = pd.DataFrame(data.read(1))
z_data.index = list(range(int(yMax), int(yMin), -1))
z_data.columns = list(range(int(xMin), int(xMax)))
z_data = z_data.applymap(lambda x: 0.5 if x < 1 else round(x, 1))

fig = go.Figure(go.Surface(z=z_data.values, x=z_data.columns, y=z_data.index, opacity=1))

for feature in features:
    fig.add_scatter3d(x=feature['X'], y=feature['Y'], z=[3] * len(v['X']),
                      mode='lines', showlegend=False,
                      line=dict(color='red', width=10)
                      )

fig.update_layout(
    title=address,
    width=900,
    height=1000,
    margin=dict(t=40, r=0, l=0, b=40),
    scene={"xaxis": {'showspikes': False},
           "yaxis": {'showspikes': False},
           "zaxis": {'showspikes': False},
           'camera_eye': {"x": 0, "y": -0.5, "z": 0.5},
           "aspectratio": {"x": 1, "y": 1, "z": 0.1}
           })