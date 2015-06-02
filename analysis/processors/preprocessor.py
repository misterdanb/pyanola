from analysis import *

import os
import toml
import numpy as np
import cv2

class PreProcessor():
    def __init__(self):
        self.config = toml.load(PREPROCESSOR_CONFIG)

    def process(self, img):
        return img

