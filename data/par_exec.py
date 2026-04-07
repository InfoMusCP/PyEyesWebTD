"""
Parameter Execute DAT

me - this DAT

Make sure the corresponding toggle is enabled in the Parameter Execute DAT.
"""

from typing import Any, List

def onValueChange(par, prev):
    # 1. Grab the current values from the parent component and convert to lowercase
    # Double-check that 'Filename' and 'Sensortype' are the exact scripting names of your custom pars
    filename = parent().par.Filename.eval().lower()
    sensor = parent().par.Sensortype.eval().lower()

    # 2. Compose the new string
    new_string = f"data/{sensor}/output/{filename}.tsv"

    # 3. Update the text component
    # Pushing this value via script will automatically fire the onValueChange in text1_callbacks
    op('chosen_data_source')[0,0] = new_string

    if sensor == "kinect":
        row = 2
    elif sensor == "qualysis" or sensor == "imu":
        row = 1
    op("camera").par.tx = op("camera_settings")[row, 0].val
    op("camera").par.ty = op("camera_settings")[row, 1].val

    if sensor == "imu":
        op("markers_source")[0,0] = f"data/qualysis/{filename}.tsv"
    else:
        op("markers_source")[0,0] = f"data/{sensor}/output/{filename}.tsv"