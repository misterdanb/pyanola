from analysis.processors.preprocessor import *

import cv2
import sys

img = cv2.imread(sys.argv[1])

pp = PreProcessor()
pp_img = PreProcessor().process(img)

cv2.imshow('pyanola', pp_img)
cv2.waitKey(0) 
