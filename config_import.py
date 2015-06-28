import xml.etree.ElementTree as ET
import glob
for xmlfile in glob.glob('*.xml'):
    tree = ET.parse(xmlfile)
    root = tree.getroot()
    config_name = None
    roll_corr_midi = None
    try:
        roll_corr_image = root[0][4][1][0][-2][0].text
    except:
        roll_corr_image = None
    try:
        roll_dm_id = root[0][0].text.split("/")[1]
    except:
        roll_dm_id = None
    try:
        roll_width = root[0][3][1][4][0][0][0][2].text
    except:
        roll_width = None
    try:
        roll_componist = root[0][3][2][2][0][1][0].text
    except:
        roll_componist=None
    try:
        roll_title = root[0][3][1][0][0][0].text
    except:
        roll_title=None
    try:
        roll_manufacturer=root[0][3][2][1][0][1][0].text
    except:
        roll_manufacturer=None
    try:
        roll_date_early=root[0][3][2][1][0][2][0][0].text
    except:
        roll_date_early=None
    try:
        roll_date_late=root[0][3][2][1][0][2][0][1].text
    except:
        roll_date_late=None
    try:
        roll_type = root[0][3][0][1][0][0].text
    except:
        roll_type=None
    if roll_type == None:
        config_name=None
    elif roll_type.split()[0] == "65":
        config_name="buffalo65.conf"
    elif roll_type.split()[0] == "88":
        config_name="buffalo88.conf"
    elif roll_type.split()[0] == "Welte":
        if roll_type.split()[1].split("/")[1] == "T100":
            config_name="welkemignont100.conf"
    else:
        config_name=None
    roll_data=[roll_dm_id, roll_title, roll_componist, roll_manufacturer, roll_width, roll_date_early, roll_date_late, config_name, roll_corr_image, roll_corr_midi]
    print(roll_data)
