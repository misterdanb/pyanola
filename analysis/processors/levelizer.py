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

        global_variances = []

        for raster_dist_test in np.linspace(min_raster_dist, max_raster_dist, self.raster_dist_test_resolution):
            for raster_offset_test in np.linspace(0, raster_dist_test, self.raster_offset_test_resolution):
                object_variances = []
                line_levels = []

                in_raster = 0

                for i in range(int(data["role_height"] / raster_dist_test)):
                    begin = data["role_top"] + raster_offset_test + i * raster_dist_test
                    end = data["role_top"] + raster_offset_test + (i + 1) * raster_dist_test

                    best_line = None
                    best_line_object_variances = None
                    best_line_variance = 0

                    # working copy
                    lines = list(data["lines"])

                    for line in lines:
                        line_object_variances = [ self._perc_in_bounds(begin, end, o) for o in line["objects"] ]

                        if best_line == None:
                            best_line = line
                            best_line_variance = sum(line_object_variances) / len(line_object_variances)
                            best_line_object_variances = line_object_variances
                        elif sum(line_object_variances) / len(line_object_variances) < best_line_variance:
                            best_line = line
                            best_line_variance = sum(line_object_variances) / len(line_object_variances)
                            best_line_object_variances = line_object_variances

                    if best_line_variance <= 0.95:
                        #object_variances += best_line_object_variances
                        object_variances.append(sum(best_line_object_variances) / len(best_line_object_variances))
                        line_levels.append((i, best_line))
                        lines.remove(best_line)
                        in_raster += 1

                if in_raster == len(data["lines"]):
                    global_variance = sum(object_variances) / len(object_variances)
                    global_variances.append((global_variance, raster_offset_test, raster_dist_test, line_levels))
                elif in_raster > len(data["lines"]):
                    print("cannot be")

        from pprint import pprint
        pprint([ (v[0], v[1], v[2]) for v in global_variances ])
        min_variance = min(global_variances, key=lambda (v, o, d, l): v)
        pprint(min_variance)

        data["raster_offset"] = min_variance[1]
        data["raster_dist"] = min_variance[2]

        for (i, matched_line) in min_variance[3]:
            for line in data["lines"]:
                if matched_line["position"] == line["position"]:
                    line["level"] = i
                    print("yay level")

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

    def _all_in_bounds(self, begin, end, objects, thresh):
        objects_in_bounds = 0

        for o in objects:
            if self._in_bounds(begin, end, o):
                objects_in_bounds += 1

        return float(objects_in_bounds) / float(len(objects)) > thresh

    def _perc_all_in_bounds(self, begin, end, objects):
        return sum([ self._perc_in_bounds(begin, end, o) for o in objects ]) / len(objects)

    def _perc_in_bounds(self, begin, end, object):
        half_dist = float(abs(end - begin)) / 2
        middle = begin + half_dist

        difference = abs(self._object_mean(object)[1] - middle)

        return difference / half_dist

    def _perc_in_bounds_old_and_not_working(self, begin, end, object):
        shift = lambda l: l[1:] + l[:1]

        parameter = lambda l, p1, p2: float(l - p1[1]) / float(p2[1] - p1[1])
        intersect = lambda l, p1, p2: (int(p1[0] + parameter(l, p1, p2) * (p2[0] - p1[0])),
                                       int(p1[1] + parameter(l, p1, p2) * (p2[1] - p1[1])))

        out = False
        in_out_lines = []

        for i in range(len(object)):
            if object[i - 1][1] < begin and object[i][1] >= begin:
                in_out_lines.append(("oi", begin, i - 1, i))
            elif object[i - 1][1] >= begin and object[i][1] < begin:
                in_out_lines.append(("io", begin, i - 1, i))
            elif object[i - 1][1] < end and object[i][1] >= end:
                in_out_lines.append(("io", end, i - 1, i))
            elif object[i - 1][1] >= end and object[i][1] < end:
                in_out_lines.append(("oi", end, i - 1, i))

        if len(in_out_lines) == 0:
            #return (1.0, object)
            # test
            return (1.0, [(0, 0)])
        elif len(in_out_lines) % 2 == 1:
            raise("There is an algorithmic error in _perc_in_bounds.")

        if in_out_lines[0][0] == "oi":
            in_out_lines = shift(in_out_lines)

        in_out_lines = [ (in_out_lines[i], in_out_lines[i + 1]) for i in range(0, len(in_out_lines), 2) ]

        # make a working copy of the object
        new_object = list(object)
        index_shift = 0

        for (bound_io, bound_oi) in in_out_lines:
            p1_io = object[bound_io[2]]
            p2_io = object[bound_io[3]]

            p1_oi = object[bound_oi[2]]
            p2_oi = object[bound_oi[3]]

            p_int_io = intersect(bound_oi[1], p1_io, p2_io)
            p_int_oi = intersect(bound_io[1], p1_oi, p2_oi)

            new_object[bound_io[3]] = p_int_io
            new_object[bound_oi[2]] = p_int_oi

            index_to = bound_io[3] - index_shift
            index_from = bound_oi[2] - index_shift

            to_p_int_io = new_object[:index_to + 1]
            from_p_int_oi = [] if index_from == 0 else new_object[index_from:]

            new_object = to_p_int_io + from_p_int_oi
            index_shift += bound_oi[2] - bound_io[3] - 1

        area = cv2.contourArea(np.asarray(object))
        new_area = cv2.contourArea(np.asarray(new_object))

        print("area before: " + str(area))
        print("area after: " + str(new_area))
        print("-----------------------------")

        return (new_area / area, new_object)

    def _in_bounds(self, begin, end, object):
        for coord in object:
            if coord[1] < begin or coord[1] >= end:
                return False

        return True
