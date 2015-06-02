from analysis import *

import os
import toml
import numpy as np
import cv2

class Levelizer():
    def __init__(self):
        self.config = toml.load(LEVELIZER_CONFIG)
        self.debug = self.config["settings"]["debug"]
        self.scanner_height = self.config["scanner"]["height"]
        self.scanner_step = self.config["scanner"]["step"]
        self.height_scale = 1

    def process(self, data):
        matched_lines = []

        last_matched = []
        falling = False

        for i in range(0, data["height"]):
            matched = self._matching_objects(i, data["objects"])

            if len(matched) < len(last_matched):
                if not falling:
                    matched_lines.append((i - 1, last_matched))
                    falling = True
            else:
                falling = False

            last_matched = matched

        return matched_lines

    def _matching_objects(self, i, objects):
        matched = []

        for o in objects:
            if self._in_bounds(i, i + self.scanner_height * self.height_scale, o):
                matched.append(o)

        return matched

    def _in_bounds(self, begin, end, object):
        for coord in object:
            if coord[0][1] < begin or coord[0][1] >= end:
                return False

        return True

