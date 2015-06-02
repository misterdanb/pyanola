from analysis import *

import os
import toml
import numpy as np
import cv2

class PreProcessor():
    def __init__(self):
        self.config = toml.load(PREPROCESSOR_CONFIG)

    def process(self, img):
        # todo: rotate image, so it's perfectly aligned horizontally
        lower_variance = np.array(self.config["thresholds"]["lower_variance"])
        upper_variance = np.array(self.config["thresholds"]["upper_variance"])

        # todo: calculate a better mean value for the background color
        bg_mean = img[10, 10]

        lower = bg_mean - lower_variance
        higher = bg_mean + upper_variance

        imgStripped = cv2.inRange(img, lower, higher)

        return imgStripped

