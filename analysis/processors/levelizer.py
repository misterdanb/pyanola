import os
import logging
import toml
import numpy as np
import operator
import log
import cv2
from math import copysign

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
        self.iterations = self.config["level_assigner"]["iterations"]
        self.exponent = self.config["level_assigner"]["mean_weight_exp"]

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

                    obj_y_means=[]

                    for obj in last_matched:
                        obj_y_positions=[ p[1] for p in obj ]
                        obj_y_means.append(sum(obj_y_positions) / float(len(obj_y_positions)))

                    line["position"] = sum(obj_y_means) / float(len(obj_y_means))
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

        phys_raster_dist = 1.0 / self.holes_per_inch * 25.4
        raster_dist = data["pixel_per_mm"] * phys_raster_dist
        """
        for i in range(10):
            lines_list=[ (l1,l2) for l1 in data["lines"] for l2 in data["lines"] if l1["position"] > l2["position"] ]
            lines_sorted=sorted(lines_list, key=lambda (l1,l2): l1["position"]-l2["position"])
            
            for (l1,l2) in lines_sorted:
                diff=l1["position"]-l2["position"]
                if diff<raster_dist/1.1:
                    data=self._merge_lines(l1,l2,data)
                else:
                    break
        """
        lines_list=[ (l1,l2) for l1 in data["lines"] for l2 in data["lines"] if l1["position"] > l2["position"] ]
        lines_sorted=sorted(lines_list, key=lambda (l1,l2): l1["position"]-l2["position"])

        last_raster_dist=raster_dist
        last_raster_offset=data["lines"][0]["position"]
        data["lines"][0]["level"]=0
        last_level=0
        for line in data["lines"][1:]:
            line["level"]=last_level+(line["position"]-last_raster_offset)/raster_dist
            last_level=line["level"]
            last_raster_offset=line["position"]

        for i in range(self.iterations):
            real_raster_dists=[]
            for line in data["lines"]:
                line["levels"]=[]

            print("Iteration " + str(i) + ":")
            print("Raster dist:"+ str(raster_dist))

            for (line1,line2) in lines_sorted:
                diff=line1["position"]-line2["position"]
                level=diff/raster_dist
                for line in data["lines"]:
                    if line1==line:
                        line["levels"].append(level+line2["level"])
                    if line2==line:
                        line["levels"].append(line1["level"]-level)
                level=int(level+.5)
                if level!=0:
                    real_raster_dists.append(diff/level)
            if len(real_raster_dists)!=0:
                raster_dist=sum(real_raster_dists)/len(real_raster_dists)

            for line in data["lines"][1:]:
                weights=map(lambda x:x**self.exponent, reversed(range(len(line["levels"]))))
                weights=map(lambda x:x/float(sum(weights)),weights)
                mean=0
                for j in range(len(line["levels"])):
                    mean+=line["levels"][j]*weights[j]
                line["level"]=int(mean+.5)
                #line["level"]=int(np.median(line["levels"])+.5)
        data["raster_dist"]=raster_dist
        return data


    def _process_stage_4(self, data):
        self.logger.info("Entering levelizing stage 4 (assigning note duration)")

        for line in data["lines"]:
            line["notes_pos"]=[]
            for obj in line["objects"]:
                x_min = min([p[0] for p in obj])
                x_max = max([p[0] for p in obj])
                line["notes_pos"].append((x_min,x_max))

            line["notes_pos"] = sorted(line["notes_pos"], key=lambda note: note[0])

            mm_per_minute = self.role_speed * 30.48
            minutes_per_pixel = 1. / (data["pixel_per_mm"] * mm_per_minute)
            ticks_per_minute = 480 * 120 #480 ticks per beat, 120 beats per minute, midos default values
            ticks_per_pixel = ticks_per_minute * minutes_per_pixel

            line["notes"] = [ ( n[0] * ticks_per_pixel, n[1] * ticks_per_pixel ) for n in line["notes_pos"] ]

        return data

    def _reduce_object(self, o):
        return reduce(lambda c1, c2: (c1[0] + c2[0], c1[1] + c2[1]), o)

    def _object_mean(self, o):
        reduced = self._reduce_object(o)

        return (float(reduced[0]) / len(o), float(reduced[1]) / len(o))

    def _object_size(self, o):
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

    def _in_bounds(self, begin, end, object):
        for coord in object:
            if coord[1] < begin or coord[1] >= end:
                return False

        return True

    def _merge_lines(self, l1, l2, data):
        for line in data["lines"]:
            if l2==line:
                line1=line
            if l1==line:
                line["objects"]+=line1["objects"]
                line["objects"]=sorted(line["objects"], key=lambda x: x[0][0])
                data["lines"].remove(l2)

                obj_y_means=[]
                for obj in line["objects"]:
                    print(obj)
                    obj_y_positions=[ p[1] for p in obj ]
                    obj_y_means.append(sum(obj_y_positions) / float(len(obj_y_positions)))

                line["position"] = sum(obj_y_means) / float(len(obj_y_means))
        return data
