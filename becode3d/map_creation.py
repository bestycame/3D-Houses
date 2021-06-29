from functions import search_address_mapbox, is_in_bbox, subsetTif
from variables import DATAS, BATI_3D
import rasterio
import pandas as pd
import plotly.graph_objects as go
import fiona


class Location:

    def __init__(self, address, boundary=100):
        self.address = address
        pos = search_address_mapbox(address, boundary=boundary, as_dict=True)
        self.x = pos['x']
        self.y = pos['y']
        self.xMin = pos['xMin']
        self.xMax = pos['xMax']
        self.yMin = pos['yMin']
        self.yMax = pos['yMax']

    def find_files(self):
        bboxes = {key: rasterio.open(next(iter(DATAS[key].values()))).bounds for key in DATAS.keys()}
        for k, bbox in bboxes.items():
            if is_in_bbox(self.xMin, self.yMin, bbox) and is_in_bbox(self.xMax, self.yMax, bbox):
                self.MNS_prov = DATAS[k]['MNS']
                self.MNT_prov = DATAS[k]['MNT']
                return True
        return 'File not found'

    def create_chm(self):
        MNS = subsetTif(self.xMin, self.xMax, self.yMin, self.yMax, self.MNS_prov).data
        MNT = subsetTif(self.xMin, self.xMax, self.yMin, self.yMax, self.MNT_prov).data
        self.CHM = (MNS - MNT)[0, :, :]

    def create_plotly_map(self):
        gdb = fiona.open(BATI_3D, layer=0)
        hits = list(gdb.items(bbox=(self.xMin, self.yMin, self.xMax, self.yMax)))

        features = []
        for hit in hits:
            features.append({'id': hit[0],
                             'H_MUR': hit[1]['properties']['H_MUR'],
                             'H_TOIT': hit[1]['properties']['H_TOIT'],
                             'E_TOIT': hit[1]['properties']['E_TOIT'],
                             'Q_LIDAR': hit[1]['properties']['Q_LIDAR'],
                             'Q_BATI': hit[1]['properties']['Q_BATI'],
                             'SHAPE_Length': hit[1]['properties']['SHAPE_Length'],
                             'SHAPE_Area': hit[1]['properties']['SHAPE_Area'],
                             'X': [int(x[0]) for x in hit[1]['geometry']['coordinates'][0][0]],
                             'Y': [int(x[1]) for x in hit[1]['geometry']['coordinates'][0][0]]})

        z_data = pd.DataFrame(self.CHM)
        z_data.index = list(range(int(self.yMax + 1), int(self.yMin), -1))
        z_data.columns = list(range(int(self.xMin), int(self.xMax + 1)))
        z_data = z_data.applymap(lambda x: 0.5 if x < 1 else round(x, 1))

        fig = go.Figure(go.Surface(z=z_data.values, x=z_data.columns, y=z_data.index, opacity=1))

        for feature in features:
            fig.add_scatter3d(x=feature['X'], y=feature['Y'], z=[3] * len(feature['X']),
                              mode='lines', showlegend=False,
                              line=dict(color='red', width=10))
        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0},
                          scene={"xaxis": {'showspikes': False},
                                 "yaxis": {'showspikes': False},
                                 "zaxis": {'showspikes': False},
                                 "camera_eye": {"x": 0, "y": -0.5, "z": 0.5},
                                 "aspectratio": {"x": 1, "y": 1, "z": 0.1}})
        fig.write_html('./test.html', full_html=False, include_plotlyjs='cdn')


if __name__ == '__main__':
    instance = Location("Rue d'Abolens 23, 4250 Boëlhe", boundary=100)
    instance.find_files()
    instance.create_chm()
    instance.create_plotly_map()
