import os
import logging
import toml
import numpy as np
import operator
import log
import cv2

class Levelizer():
    CONFIG_FILE = "levelizer.conf"
    
    def __init__(self):
        self.config = toml.load(Levelizer.CONFIG_FILE)
        self.logger = logging.getLogger("pyanola.analysis.levelizer")
        self.debug = self.config["settings"]["debug"]

        if self.debug:
            self.logger.setLevel(logging.DEBUG)

        self.scanner_height_scale = self.config["scanner"]["height_scale"]
        self.scanner_step = self.config["scanner"]["step"]
        self.height_scale = 1

    def process(self, data):
        self._prepare(data)
        matched = self._process_stage_1(data)
        matched = self._process_stage_2(matched)

        return matched

    def _prepare(self, data):
        self.scanner_height = max([
            (max([ e[1] for e in o ]) -
             min([ e[1] for e in o ])) for o in data["objects"]
        ])

    def _process_stage_1(self, data):
        self.logger.info("Entering levelizing stage 1 (matching lines)")

        matched_lines = []

        last_matched = []
        falling = False

        for i in range(0, data["height"], self.scanner_step):
            matched = self._matching_objects(i, data["objects"])

            if len(matched) < len(last_matched):
                if not falling:
                    matched_lines.append((i - 1, last_matched))
                    falling = True
            else:
                falling = False

            last_matched = matched

        data["lines"] = matched_lines

        return data

    def _process_stage_2(self, data):
        self.logger.info("Entering levelizing stage 2 (rescue lost objects)")

        lines_only = map(lambda x: x[1], data["lines"])
        matched_objects = reduce(operator.add, lines_only)
        lost_objects = [ x for x in data["objects"] if x not in matched_objects ]

        self.logger.info("Objects: " + str(len(data["objects"])) + "\n" +
                         "Matched: " + str(len(matched_objects)) + "\n" +
                         "Lost: " + str(len(lost_objects)))

        reduce_object = lambda o: reduce(lambda c1, c2: (c1[0] + c2[0], c1[1] + c2[1]), o)
        mean_y = lambda o: float(reduce_object(o)[1]) / len(o)

        for o in lost_objects:
            min_val = data["height"]
            min_line = None

            mean_object_y = mean_y(o)

            for l in data["lines"]:
                mean_line_y = reduce(lambda y1, y2:
                    y1 + y2, map(lambda lo:
                        mean_y(lo), l[1])) / len(l[1])
                mean_y_dist = abs(mean_object_y - mean_line_y)

                if mean_y_dist < min_val:
                    min_val = mean_y_dist
                    min_line = l

            if min_line != None:
                min_line[1].append(o)

        return data

    def _matching_objects(self, i, objects):
        matched = []

        for o in objects:
            if self._in_bounds(i, i + self.scanner_height * self.scanner_height_scale, o):
                matched.append(o)

        return matched

    def _in_bounds(self, begin, end, object):
        for coord in object:
            if coord[1] < begin or coord[1] >= end:
                return False

        return True

