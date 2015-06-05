from analysis import *

import os
import toml
import numpy as np
import cv2

class Analyzer():
    def __init__(self):
        self.config = toml.load(ANALYZER_CONFIG)
        self.debug = self.config["settings"]["debug"]

    def process(self, img):
        # todo: rotate image, so it's perfectly aligned horizontally
        lower_variance = np.array(self.config["thresholds"]["lower_variance"])
        upper_variance = np.array(self.config["thresholds"]["upper_variance"])

        # todo: calculate a better mean value for the background color
        bg_mean = img[10, 10]

        lower = bg_mean - lower_variance
        higher = bg_mean + upper_variance

        imgStripped = cv2.inRange(img, lower, higher)

        if self.debug:
            cv2.imshow('stripped image', imgStripped)
            cv2.waitKey(0)

        contours, h = cv2.findContours(imgStripped, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        convex_contours = [ cv2.convexHull(c) for c in contours ]

        coords_only = [ [ (e[0][0], e[0][1]) for e in c ] for c in convex_contours ]

        return { "width": img.shape[1], \
                 "height": img.shape[0], \
                 "objects": coords_only }

