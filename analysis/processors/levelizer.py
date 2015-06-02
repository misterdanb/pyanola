from analysis import *

import os
import toml
import numpy as np
import cv2

class Levelizer():
    def __init__(self):
        self.config = toml.load(LEVELIZER_CONFIG)

    def process(self, data):
        return data

