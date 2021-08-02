from becode3d.functions import search_address_mapbox, is_in_bbox, subsetTif
from becode3d.variables import DATAS, BATI_3D
import rasterio
import pandas as pd
import plotly.graph_objects as go
import fiona
import pickle
from os.path import join, dirname
from dotenv import load_dotenv

env_path = join(dirname(dirname(__file__)), ".env")
load_dotenv(dotenv_path=env_path)


class Location:
    def __init__(self, address, boundary=100):
        self.address = address
        self.boundary = boundary
        pos = search_address_mapbox(address, boundary=boundary, as_dict=True)
        self.x = pos["x"]
        self.y = pos["y"]
        self.xMin = pos["xMin"]
        self.xMax = pos["xMax"]
        self.yMin = pos["yMin"]
        self.yMax = pos["yMax"]
        self.address = pos["address"]

    def find_files(self):
        """
        This function will return to correct MNS/MNT TIFF file
        for the province where the address is located
        """
        bboxes = {
            key: rasterio.open(next(iter(DATAS[key].values()))).bounds
            for key in DATAS.keys()
        }
        for k, bbox in bboxes.items():
            if is_in_bbox(self.xMin, self.yMin, bbox) and is_in_bbox(
                self.xMax, self.yMax, bbox
            ):
                self.MNS_prov = DATAS[k]["MNS"]
                self.MNT_prov = DATAS[k]["MNT"]
                return True
        return "File not found"

    def create_chm(self):
        '''
        This function will create the CHM based on the MNS and MNT tiff files
        '''
        MNS = subsetTif(
            self.xMin, self.xMax, self.yMin, self.yMax, self.MNS_prov
        ).data
        MNT = subsetTif(
            self.xMin, self.xMax, self.yMin, self.yMax, self.MNT_prov
        ).data
        self.CHM = (MNS - MNT)[0, :, :]

    def create_plotly_map(self):
        '''
        This function will plot the CHM on a Plotly Suface 3D plot,
        extract the buildings and features from the BATI_3D GDB file.
        It will save the data as an instance and to a html+picker for a small cache system.
        '''
        gdb = fiona.open(BATI_3D, layer=0)
        hits = list(
            gdb.items(bbox=(self.xMin, self.yMin, self.xMax, self.yMax))
        )

        features = []
        for hit in hits:
            features.append(
                {
                    "H_MUR": hit[1]["properties"]["H_MUR"],
                    "H_TOIT": hit[1]["properties"]["H_TOIT"],
                    "E_TOIT": hit[1]["properties"]["E_TOIT"],
                    "Q_LIDAR": hit[1]["properties"]["Q_LIDAR"],
                    "Q_BATI": hit[1]["properties"]["Q_BATI"],
                    "SHAPE_Length": hit[1]["properties"]["SHAPE_Length"],
                    "SHAPE_Area": hit[1]["properties"]["SHAPE_Area"],
                    "X": [
                        int(x[0])
                        for x in hit[1]["geometry"]["coordinates"][0][0]
                    ],
                    "Y": [
                        int(x[1])
                        for x in hit[1]["geometry"]["coordinates"][0][0]
                    ],
                }
            )

        z_data = pd.DataFrame(self.CHM)
        z_data.index = list(range(int(self.yMax + 1), int(self.yMin), -1))
        z_data.columns = list(range(int(self.xMin), int(self.xMax + 1)))

        fig = go.Figure(
            go.Surface(
                z=z_data,
                x=z_data.columns,
                y=z_data.index,
                hoverinfo="skip",
                cmin=-0,
                cmid=7,
                cmax=15,
            )
        )

        for feature in features:
            fig.add_scatter3d(
                x=feature["X"],
                y=feature["Y"],
                z=[5] * len(feature["X"]),
                mode="lines",
                showlegend=False,
                opacity=0.7,
                hovertemplate="Building Found!<extra></extra>",
                line={"color": "red", "width": 7},
                surfaceaxis=1,
                visible=True,
            )

        fig.update_layout(
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            scene={
                "camera_eye": {"x": 0, "y": -0.5, "z": 0.5},
                "aspectratio": {"x": 1, "y": 1, "z": 0.1},
            },
        )
        fig.update_scenes(
            xaxis_range=(self.xMin, self.xMax),
            yaxis_range=(self.yMin, self.yMax),
        )

        fig.write_html(
            f"./templates/maps/{self.x}x{self.y}y{self.boundary}.html",
            full_html=False,
            include_plotlyjs="cdn",
        )
        with open(
            f"./templates/maps/{self.x}x{self.y}y{self.boundary}.pickle", "wb"
        ) as handle:
            pickle.dump(features, handle, protocol=pickle.HIGHEST_PROTOCOL)
        div = fig.to_html(full_html=False, include_plotlyjs="cdn")
        return div, features


if __name__ == "__main__":
    instance = Location("1 Rue de Crehen Hannut", boundary=100)
    instance.find_files()
    instance.create_chm()
    instance.create_plotly_map()
