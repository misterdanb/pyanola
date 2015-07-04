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

        #
        # find the two big areas in the top and the bottom corner of the image
        # and calculate the mean background color
        #
        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # find brightest and darkest pixel of the image
        gray_pixel_list = [ int(p) for row in gray_img for p in row ]
        bright_gray = max(gray_pixel_list)
        dark_gray = min(gray_pixel_list)
        mean_gray = sum(gray_pixel_list) / len(gray_pixel_list)

        thresh_gray = (bright_gray + dark_gray) / 2
        mode = cv2.THRESH_BINARY if mean_gray < thresh_gray else cv2.THRESH_BINARY_INV

        _, threshed = cv2.threshold(gray_img, thresh_gray, 255, mode)

        basic_contours, _ = cv2.findContours(threshed, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        basic_contours = [ cv2.convexHull(c) for c in basic_contours ]

        basic_mean_area = reduce(operator.add, [ cv2.contourArea(c) for c in basic_contours ]) / len(basic_contours)
        _, big = self._separate_big_objects(basic_contours, basic_mean_area)

        # calculate the role height and get the big bars
        bg_bars = None

        if len(big) >= 2:
            big_sorted = sorted(big, key=lambda c: cv2.contourArea(c))
            bg_bars = big_sorted[-2:]

        role_height = None

        if bg_bars != None:
            sorted_bars = sorted(bg_bars, key=lambda b: b[0][0][1])
            bars_y = [ [ c[0][1] for c in b ] for b in sorted_bars ]
            role_top = max(bars_y[0])
            role_bottom = min(bars_y[1])
            role_height = role_bottom-role_top

        if self.debug:
            cv2.imshow("threshed image", threshed)
            cv2.waitKey(0)

        # calculate the mean of the pixels masked by the big bars
        pixel_sum = [ 0, 0, 0 ]
        pixel_count = 0

        bar1_min = min(bg_bars[0], key=lambda p: p[0][0] + p[0][1])
        bar1_max = max(bg_bars[0], key=lambda p: p[0][0] + p[0][1])

        for x in range(bar1_min[0][0], bar1_max[0][0]):
            for y in range(bar1_min[0][1], bar1_max[0][1]):
                pixel_sum[0] += img[y, x][0]
                pixel_sum[1] += img[y, x][1]
                pixel_sum[2] += img[y, x][2]
                pixel_count += 1

        bar2_min = min(bg_bars[1], key=lambda p: p[0][0] + p[0][1])
        bar2_max = max(bg_bars[1], key=lambda p: p[0][0] + p[0][1])

        for x in range(bar2_min[0][0], bar2_max[0][0]):
            for y in range(bar2_min[0][1], bar2_max[0][1]):
                pixel_sum[0] += img[y, x][0]
                pixel_sum[1] += img[y, x][1]
                pixel_sum[2] += img[y, x][2]
                pixel_count += 1

        bg_mean = [ pixel_sum[0] / pixel_count, pixel_sum[1] / pixel_count, pixel_sum[2] / pixel_count ]

        width = img.shape[1]
        height = img.shape[0]

        top_left=max(sorted_bars[0], key=lambda p:p[0][1]-p[0][0])[0]
        top_right=max(sorted_bars[0], key=lambda p:p[0][1]+p[0][0])[0]

        bottom_left=min(sorted_bars[1], key=lambda p:p[0][1]+p[0][0])[0]
        bottom_right=min(sorted_bars[1], key=lambda p:p[0][1]-p[0][0])[0]

        bars_y = [ [ c[0][1] for c in b ] for b in sorted_bars ]

        distorted = np.array([top_left,
                              top_right,
                              bottom_right,
                              bottom_left],dtype="float32")
       
        top_left[1]=.5*(top_left[1]+top_right[1])
        top_right[1]=top_left[1]

        bottom_left[1]=.5*(bottom_left[1]+bottom_right[1])
        bottom_right[1]=bottom_left[1]

        correct = np.array([top_left,
                              top_right,
                              bottom_right,
                              bottom_left],dtype="float32")

        mat=cv2.getPerspectiveTransform(distorted,correct)

        if self.debug:
            cv2.imshow("stripped image", img)
            cv2.waitKey(0)

        img=cv2.warpPerspective(img,mat,(width,height))

        if self.debug:
            cv2.imshow("stripped image", img)
            cv2.waitKey(0)

        #
        # find, given the background mean color, the contours, which are candidates
        # to be notes
        #
        # todo: rotate image, so it's perfectly aligned horizontally
        lower_variance = np.array(self.config["thresholds"]["lower_variance"])
        upper_variance = np.array(self.config["thresholds"]["upper_variance"])

        lower = bg_mean - lower_variance
        higher = bg_mean + upper_variance

        imgStripped = cv2.inRange(img, lower, higher)

        if self.debug:
            cv2.imshow("stripped image", imgStripped)
            cv2.waitKey(0)

        if "blur_amount" in self.config["thresholds"]:
            imgStripped = cv2.GaussianBlur(imgStripped, (self.config["thresholds"]["blur_amount"], 1), 0)
            _, imgStripped = cv2.threshold(imgStripped, self.config["thresholds"]["blur_threshold"], 255, cv2.THRESH_BINARY)

        if self.debug:
            cv2.imshow("stripped image", imgStripped)
            cv2.waitKey(0)

        contours, h = cv2.findContours(imgStripped, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = [ cv2.convexHull(c) for c in contours ]

        mean_area = reduce(operator.add, [ cv2.contourArea(c) for c in contours ]) / len(contours)

        if self.config["thresholds"]["remove_big_objects"]:
            contours, _ = self._separate_big_objects(contours, mean_area)

        if self.config["thresholds"]["remove_small_objects"]:
            contours, _ = self._separate_small_objects(contours, mean_area)

        coords_only = [ [ (e[0][0], e[0][1]) for e in c ] for c in contours ]

        data = {}

        data["width"] = width
        data["height"] = height


        if role_height != None:
            data["role_height"] = role_height
        if role_top != None:
            data["role_top"] = role_top

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
