import os
import logging
import toml
import numpy as np
import operator
import log
import cv2

class Levelizer():
    CONFIG_FILE = "levelizer.conf"
    SPECS_FILE = ".specs.conf"

    def __init__(self):
        self.config = toml.load(Levelizer.CONFIG_FILE)
        self.logger = logging.getLogger("pyanola.analysis.levelizer")
        self.debug = self.config["settings"]["debug"]

        if self.debug:
            self.logger.setLevel(logging.DEBUG)

        self.scanner_height_scale = self.config["scanner"]["height_scale"]
        self.scanner_step = self.config["scanner"]["step"]
        self.raster_dist_variance = self.config["level_assigner"]["dist_variance"]
        self.raster_offset_test_resolution = self.config["level_assigner"]["offset_test_resolution"]
        self.raster_dist_test_resolution = self.config["level_assigner"]["dist_test_resolution"]
        self.raster_match_percentage = self.config["level_assigner"]["match_percentage"]
        self.raster_line_match_percentage = self.config["level_assigner"]["line_match_percentage"]

        self.specs = toml.load(Levelizer.SPECS_FILE)
        self.phys_role_height = self.specs["role"]["height"]
        self.holes_per_inch = self.specs["role"]["holes_per_inch"]
        self.role_speed = self.specs["role"]["speed"]

    def process(self, data):
        self._prepare(data)
        matched = self._process_stage_1(data)
        matched = self._process_stage_2(matched)
        mapped_lines = self._process_stage_3(matched)
        mapped_lines = self._process_stage_4(mapped_lines)

        return mapped_lines

    def _prepare(self, data):
        self.scanner_height = max([
            self._object_size(o)[1] for o in data["objects"]
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
                    line = {}

                    line["position"] = i - 1
                    line["objects"] = last_matched

                    matched_lines.append(line)

                    falling = True
            else:
                falling = False

            last_matched = matched

        data["lines"] = matched_lines

        return data

    def _process_stage_2(self, data):
        self.logger.info("Entering levelizing stage 2 (rescue lost objects)")

        line_objects_only = [ x["objects"] for x in data["lines"] ]
        matched_objects = reduce(operator.add, line_objects_only)
        lost_objects = [ x for x in data["objects"] if x not in matched_objects ]

        self.logger.info("Objects: " + str(len(data["objects"])) + "\n" +
                         "Matched: " + str(len(matched_objects)) + "\n" +
                         "Lost: " + str(len(lost_objects)))

        for o in lost_objects:
            min_val = data["height"]
            min_line = None

            mean_object_y = self._object_mean(o)[1]

            for l in data["lines"]:
                mean_line_y = reduce(lambda y1, y2:
                    y1 + y2, map(lambda lo:
                        self._object_mean(lo)[1], l["objects"])) / len(l["objects"])
                mean_y_dist = abs(mean_object_y - mean_line_y)

                if mean_y_dist < min_val:
                    min_val = mean_y_dist
                    min_line = l

            if min_line != None:
                min_line["objects"].append(o)

        return data

    def _process_stage_3(self, data):
        self.logger.info("Entering levelizing stage 3 (assigning levels)")

        data["pixel_per_mm"] = data["role_height"] / self.phys_role_height

        phys_raster_dist= 1. / self.holes_per_inch * 25.4
        raster_dist = data["pixel_per_mm"] * phys_raster_dist

        min_raster_dist = raster_dist - self.raster_dist_variance
        max_raster_dist = raster_dist + self.raster_dist_variance

        matched_raster_offset, matched_raster_dist = None, None

        for raster_dist_test in np.linspace(min_raster_dist, max_raster_dist, self.raster_dist_test_resolution):
            if matched_raster_offset != None and matched_raster_dist != None:
                break

            for raster_offset_test in np.linspace(0, raster_dist_test, self.raster_offset_test_resolution):
                in_raster = 0

                for i in range(int(data["role_height"] / raster_dist)):
                    begin = raster_offset_test + i * raster_dist_test
                    end = raster_offset_test + (i + 1) * raster_dist_test
                    #print("  begin: " + str(begin))
                    #print("  end: " + str(end))

                    for line in data["lines"]:
                        in_raster_line = 0

                        if self._all_in_bounds(begin, end, line["objects"], self.raster_line_match_percentage):
                            in_raster += 1
                            in_raster_line += 1
                            # actually we can break here, right?
                            # we want to have solutions, where raster_dist is as small as possible
                            break

                        if in_raster_line > 1:
                            self.logger.error("Two lines matching one raster line!")

                if float(in_raster) / float(len(data["lines"])) > self.raster_match_percentage:
                    matched_raster_offset = raster_offset_test
                    matched_raster_dist = raster_dist_test
                    break

        print(raster_dist)
        print(matched_raster_dist)

        data["raster_offset"] = matched_raster_offset
        data["raster_dist"] = matched_raster_dist

        for line in data["lines"]:
            line["level"] = (line["position"] - data["role_top"]) / matched_raster_dist

        return data

    def _process_stage_4(self, data):
        self.logger.info("Entering levelizing stage 4 (assigning note duration)")

        for line in data["lines"]:
            line["notes"]=[]
            for obj in line["objects"]:
                x_min = min([p[0] for p in obj])
                x_max = max([p[0] for p in obj])
                line["notes"].append((x_min,x_max))

            line["notes"] = sorted(line["notes"], key=lambda note: note[0])

            mm_per_minute = self.role_speed * 30.48
            minutes_per_pixel = 1. / (data["pixel_per_mm"] * mm_per_minute)
            ticks_per_minute = 480 * 120 #480 ticks per beat, 120 beats per minute, midos default values
            ticks_per_pixel = ticks_per_minute * minutes_per_pixel

            line["notes"] = [ ( n[0] * ticks_per_pixel, n[1] * ticks_per_pixel ) for n in line["notes"] ]

        return data

    def _reduce_object(self, o):
        return reduce(lambda c1, c2: (c1[0] + c2[0], c1[1] + c2[1]), o)

    def _object_mean(self, o):
        reduced = self._reduce_object(o)

        return (float(reduced[0]) / len(o), float(reduced[1]) / len(o))

    def _object_size(sefl, o):
        object_x_values = [ c[0] for c in o ]
        object_y_values = [ c[1] for c in o ]

        width = max(object_x_values) - min(object_x_values)
        height = max(object_y_values) - min(object_y_values)

        return (width, height)

    def _matching_objects(self, begin, objects):
        matched = []

        for o in objects:
            if self._in_bounds(begin, begin + self.scanner_height * self.scanner_height_scale, o):
                matched.append(o)

        return matched

    def _all_in_bounds(self, begin, end, objects, thresh):
        objects_in_bounds = 0

        for o in objects:
            if self._in_bounds(begin, end, o):
                objects_in_bounds += 1

        return float(objects_in_bounds) / float(len(objects)) > thresh

    def _in_bounds(self, begin, end, object):
        for coord in object:
            if coord[1] < begin or coord[1] >= end:
                return False

        return True
