import os
import logging
import toml
import numpy as np
import operator
import cv2

class Analyzer():
    CONFIG_FILE= "analyzer.conf"

    METHOD_BACKGROUND_RECONITION = "background_recognition"

    def __init__(self):
        self.config = toml.load(Analyzer.CONFIG_FILE)
        self.logger = logging.getLogger("pyanola.analysis.analyzer")
        self.debug = self.config["settings"]["debug"]

        if self.debug:
            self.logger.setLevel(logging.DEBUG)

    def process(self, img):
        if self.config["settings"]["method"] == Analyzer.METHOD_BACKGROUND_RECONITION:
            return self._process_background_recognition(img)
        else:
            raise("No such analyzing method!")

    def _process_background_recognition(self, img):
        self.logger.info("Entering analyzing stage")

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
        contours = [ cv2.convexHull(c) for c in contours ]

        mean_area = reduce(operator.add, [ cv2.contourArea(c) for c in contours ]) / len(contours)

        if self.config["thresholds"]["remove_big_objects"]:
            contours = self._remove_big_objects(contours, mean_area)

        if self.config["thresholds"]["remove_small_objects"]:
            contours = self._remove_small_objects(contours, mean_area)

        coords_only = [ [ (e[0][0], e[0][1]) for e in c ] for c in contours ]

        return { "width": img.shape[1], \
                 "height": img.shape[0], \
                 "objects": coords_only }

    def _remove_big_objects(self, contours, mean_area):
        max_area_factor = self.config["thresholds"]["max_area_factor"]
        without_big = [ c for c in contours if cv2.contourArea(c) < max_area_factor * mean_area]

        return without_big

    def _remove_small_objects(self, contours, mean_area):
        min_area_factor = self.config["thresholds"]["min_area_factor"]
        without_small = [ c for c in contours if cv2.contourArea(c) > min_area_factor * mean_area]

        return without_small

