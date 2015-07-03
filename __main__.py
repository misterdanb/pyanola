from analysis.processors.preprocessor import *
from analysis.processors.analyzer import *
from analysis.processors.levelizer import *
from conversion.converters.midigenerator import *
import log
import copy

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

#cv2.imshow('detected role structure', p_img)
#cv2.waitKey(0)

p_img_old=copy.deepcopy(p_img)
last_level=0
last_position=l_data["lines"][0]["position"]

for line in l_data["lines"]:
    print("##############################################")
    if "level" in line:
        print("### level: " + str(line["level"]))
        print("### position: " + str(line["position"]))
    else:
        print("### level: NO LEVEL")
        print("### position: " + str(line["position"]))
    print("##############################################")

    p_img=copy.deepcopy(p_img_old)

    p1 = (0, int(line["position"]+.5))
    p2 = (l_data["width"], int(line["position"]+.5))
    cv2.line(p_img, p1, p2, (0, 255, 0))
    p1 = (0, int(last_position+.5))
    p2 = (l_data["width"], int(last_position+.5))
    cv2.line(p_img, p1, p2, (0, 255, 0))

    for i in range(line["level"]-last_level+1):
        p1 = (0,int(last_position+i*l_data["raster_dist"]+.5))
        p2 = (l_data["width"],int(last_position+i*l_data["raster_dist"]+.5))
        cv2.line(p_img, p1, p2, (0, 0, 255))

    for c in line["objects"]:
        npc = np.array([ [[e[0], e[1]]] for e in c ])
        cv2.drawContours(p_img, [npc], 0, (0, 255, 0), -1)

    for note in line["notes_pos"]:
        p1 = (int(note[0]), 0)
        p2 = (note[0], 1000)
        cv2.line(p_img, p1, p2, (0, 0, 255))
        p1 = (note[1], 0)
        p2 = (note[1], 1000)
        cv2.line(p_img, p1, p2, (255, 0, 0))
        cv2.imshow('detected role structure', p_img)
        cv2.waitKey(0)

        
    last_level=line["level"]
    last_position=line["position"]

    """
    for i in range(int(l_data["height"] / l_data["raster_dist"])):
        p1 = (0, int(l_data["raster_offset"]+l_data["raster_dist"]*i))
        p2 = (l_data["width"], int(l_data["raster_offset"]+l_data["raster_dist"]*i))
        cv2.line(p_img, p1, p2, (0, 0, 255))
    """
    #cv2.imshow('detected role structure', p_img)
    #cv2.waitKey(0)
