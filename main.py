from analysis.processors.preprocessor import *
from analysis.processors.analyzer import *
from analysis.processors.levelizer import *

import cv2
import sys

img = cv2.imread(sys.argv[1])

preprocessor = PreProcessor()
p_img = preprocessor.process(img)

analyzer = Analyzer()
a_data = analyzer.process(p_img)

levelizer = Levelizer()
l_data = levelizer.process(a_data)

#for c in a_data["objects"]:
#    cv2.drawContours(img, [c], 0, (0, 255, 0), -1)

cv2.imshow('detected role structure', img)
cv2.waitKey(0)

for line in l_data["lines"]:
    print("##############################################")
    print("### " + str(line[0]))
    print("##############################################")

    for c in line[1]:
        npc = np.array([ [[e[0], e[1]]] for e in c ])
        cv2.drawContours(img, [npc], 0, (0, 0, 0), -1)

    cv2.imshow('detected role structure', img)
    cv2.waitKey(0) 
