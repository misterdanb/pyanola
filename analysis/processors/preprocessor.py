import os
import logging
import toml
import numpy as np
import cv2

class Preprocessor():
    CONFIG_FILE = "preprocessor.conf"

    def __init__(self):
        self.config = toml.load(Preprocessor.CONFIG_FILE)
        self.logger = logging.getLogger("pyanola.analysis.preprocessor")
        self.debug = self.config["settings"]["debug"]
        self.blur = self.config["settings"]["blur"]
        self.blur_amount = self.config["settings"]["blur_amount"]
        self.flipped = self.config["settings"]["flipped"]

        if self.debug:
            self.logger.setLevel(logging.DEBUG)

    def process(self, img):
        self.logger.info("Entering preprocesing stage")

        if self.blur:
            img = cv2.GaussianBlur(img, (self.blur_amount, 1), 0)

        if self.flipped:
            for i in range(len(img)):
                img[i]=img[i][::-1]

        return img
