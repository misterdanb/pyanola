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

        if self.debug:
            self.logger.setLevel(logging.DEBUG)

    def process(self, img):
        self.logger.info("Entering preprocesing stage")

        return img

