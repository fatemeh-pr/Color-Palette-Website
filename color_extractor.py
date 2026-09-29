import colorsys
import numpy as np
import pandas as pd
from PIL import Image
from sklearn.cluster import KMeans

DEFAULT_CLUSTERS = 20


class ColorExtractor:
    def __init__(self):
        self.filepath = ""
        self.image = None
        self.image_array = np.empty([3, 3], dtype=np.int8)
        self.image_data = pd.DataFrame()
        self.top_colors = pd.DataFrame()

    def process_image(self, img_path):
        self.filepath = img_path
        self.image = Image.open(self.filepath).convert('RGB')
        self.image_array = np.array(self.image).reshape(-1, 3)
        self.image_data = pd.DataFrame(columns=["RGB", "HSL", "Code", "Count", "Percentage", "Group"])
        self.top_colors = pd.DataFrame()
        self.prepare_image_data()

    def prepare_image_data(self):
        self.image_data["RGB"] = [tuple(rgb.tolist()) for rgb in self.image_array]
        self.image_data["HSL"] = [self.convert_rgb_to_hsl(rgb_color) for rgb_color in self.image_data["RGB"]]
        self.image_data["Code"] = [self.convert_rgb_to_code(rgb_color) for rgb_color in self.image_data["RGB"]]
        self.image_data["Count"] = self.image_data.groupby("Code")["Code"].transform("count")

    def convert_rgb_to_code(self, color):
        r, g, b = color
        code = f"#{r:02x}{g:02x}{b:02x}"
        return code

    def convert_rgb_to_hsl(self, color):
        r, g, b = color
        one_255 = 1.0 / 255.0
        h, l, s = colorsys.rgb_to_hls(r * one_255, g * one_255, b * one_255)
        hsl = (round(h * 360.0), round(s * 100.0), round(l * 100.0))
        return hsl

    def cluster_colors(self):
        kmeans = KMeans(n_clusters=DEFAULT_CLUSTERS,
                        init='k-means++',
                        random_state=42)
        kmeans.fit(self.image_array)
        self.image_data["Group"] = kmeans.labels_
        self.image_data["Group Size"] = self.image_data.groupby("Group").transform("size")
        self.image_data["Percentage"] = ((self.image_data["Group Size"] / len(self.image_data)) * 100).round(4)

    def extract_colors(self, n_colors):
        self.cluster_colors()
        top_clusters_labels = self.image_data.groupby("Group").size().sort_values(ascending=False).head(n_colors).index
        top_clusters_rows = self.image_data[self.image_data["Group"].isin(top_clusters_labels.tolist())]
        top_colors_idx = top_clusters_rows.groupby("Group")["Count"].idxmax()

        self.top_colors = self.image_data.loc[top_colors_idx].sort_values(by="Percentage", ascending=False)
        self.top_colors.reset_index(inplace=True)
        return self.top_colors

    def save_csv(self, path):
        colors_data = self.top_colors[["RGB", "HSL", "Code", "Percentage"]]
        colors_data.to_csv(path, index=False)
