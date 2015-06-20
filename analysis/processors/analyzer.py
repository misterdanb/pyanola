import os
import logging
import toml
import numpy as np
import operator
import itertools
import cv2

class Analyzer():
    CONFIG_FILE = "analyzer.conf"

    METHOD_BACKGROUND_RECONITION = "background_recognition"
    METHOD_CANNY_EDGES = "canny_edges"

    def __init__(self):
        self.config = toml.load(Analyzer.CONFIG_FILE)
        self.logger = logging.getLogger("pyanola.analysis.analyzer")
        self.debug = self.config["settings"]["debug"]

        if self.debug:
            self.logger.setLevel(logging.DEBUG)

    def process(self, img):
        self.logger.info("Entering analyzing stage")

        if self.config["settings"]["method"] == Analyzer.METHOD_BACKGROUND_RECONITION:
            return self._process_background_recognition(img)
        elif self.config["settings"]["method"] == Analyzer.METHOD_CANNY_EDGES:
            return self._process_canny_edges(img)
        else:
            raise("No such analyzing method!")

    def _process_background_recognition(self, img):
        self.logger.info("Using method \"background recognition\"")

        # todo: rotate image, so it's perfectly aligned horizontally
        lower_variance = np.array(self.config["thresholds"]["lower_variance"])
        upper_variance = np.array(self.config["thresholds"]["upper_variance"])

        # todo: calculate a better mean value for the background color
        bg_mean = img[10, 10]

        lower = bg_mean - lower_variance
        higher = bg_mean + upper_variance

        imgStripped = cv2.inRange(img, lower, higher)

        if self.debug:
            cv2.imshow("stripped image", imgStripped)
            cv2.waitKey(0)

        contours, h = cv2.findContours(imgStripped, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = [ cv2.convexHull(c) for c in contours ]

        mean_area = reduce(operator.add, [ cv2.contourArea(c) for c in contours ]) / len(contours)

        if self.config["thresholds"]["remove_big_objects"]:
            contours, big = self._separate_big_objects(contours, mean_area)
        else:
            _, big = self._separate_big_objects(contours, mean_area)

        if self.config["thresholds"]["remove_small_objects"]:
            contours, small = self._separate_small_objects(contours, mean_area)

        coords_only = [ [ (e[0][0], e[0][1]) for e in c ] for c in contours ]

        # calculate the role height
        bg_bars = None

        if len(big) >= 2:
            big_sorted = sorted(big, key=lambda c: cv2.contourArea(c))
            bg_bars = big_sorted[-2:]

        role_height = None

        if bg_bars != None:
            bar_pairs = itertools.product(bg_bars[0], bg_bars[1])
            bar_diffs = [ abs(p1[0][1] - p2[0][1]) for (p1, p2) in bar_pairs ]
            role_height = min(bar_diffs)

        data = {}

        data["width"] = img.shape[1]
        data["height"] = img.shape[0]

        if role_height != None:
            data["role_height"] = role_height

        data["objects"] = coords_only

        self.logger.info("Image size: " + str(data["width"]) + "x" + str(data["height"]) + "\n" +
                         "Role height: " + str(data["role_height"]))

        return data

    def _process_canny_edges(self, img):
        # DO NOT USE RIGHT NOW
        self.logger.info("Using method \"canny edges\"")

        imgGray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(imgGray, 120, 140)

        if self.debug: 
            cv2.imshow("canny image", edges)
            cv2.waitKey(0)

        contours, h = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            cv2.drawContours(img, [contour], 0, (0, 0, 255), 3)
            cv2.imshow("", img)
            cv2.waitKey(0)

        cv2.imshow("", img)
        cv2.waitKey(0)

    def _separate_big_objects(self, contours, mean_area):
        max_area_factor = self.config["thresholds"]["max_area_factor"]
        without_big = [ c for c in contours if cv2.contourArea(c) < max_area_factor * mean_area]
        big = [ c for c in contours if cv2.contourArea(c) >= max_area_factor * mean_area]

        return (without_big, big)

    def _separate_small_objects(self, contours, mean_area):
        min_area_factor = self.config["thresholds"]["min_area_factor"]
        without_small = [ c for c in contours if cv2.contourArea(c) > min_area_factor * mean_area]
        small = [ c for c in contours if cv2.contourArea(c) <= min_area_factor * mean_area]

        return (without_small, small)

