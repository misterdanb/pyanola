from analysis.processors.preprocessor import *
from analysis.processors.analyzer import *
from analysis.processors.levelizer import *
from conversion.converters.midigenerator import *
import log

import cv2
import sys

log.init_logger()

img = cv2.imread(sys.argv[1])

preprocessor = Preprocessor()
p_img = preprocessor.process(img)

analyzer = Analyzer()
a_data = analyzer.process(p_img)

levelizer = Levelizer()
l_data = levelizer.process(a_data)

midi_generator = MidiGenerator()
m_data = midi_generator.create(l_data)

#for c in a_data["objects"]:
#    cv2.drawContours(img, [c], 0, (0, 255, 0), -1)

cv2.imshow('detected role structure', img)
cv2.waitKey(0)

for line in l_data["lines"]:
    print("##############################################")
    print("### " + str(line["level"]))
    print("##############################################")
    #print(line[1])

    for c in line["objects"]:
        npc = np.array([ [[e[0], e[1]]] for e in c ])
        cv2.drawContours(img, [npc], 0, (0, 255, 0), -1)
    """
    for note in line["notes"]:
        p1 = (note[0], 0)
        p2 = (note[0], 1000)
        cv2.line(img, p1, p2, (0, 0, 255))
        p1 = (note[1], 0)
        p2 = (note[1], 1000)
        cv2.line(img, p1, p2, (255, 0, 0))
    """
    """
    for i in range(0, 1000):
        p1 = (0, l_data["raster_pos"]+(l_data["raster_dist"]+levelizer.scanner_height)*i)
        p2 = (800, l_data["raster_pos"]+(l_data["raster_dist"]+levelizer.scanner_height)*i)
        cv2.line(img, p1, p2, (0, 0, 255))
    """

    cv2.imshow('detected role structure', img)
    cv2.waitKey(0)
