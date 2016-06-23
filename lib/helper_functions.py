import traceback
import struct
import os
from math import radians, atan2, degrees, sin, cos, sqrt

from PyQt5.QtGui import QPicture, QPainter, QImage, QColor, QPixmap

MODEL_ATTR = {
    "sAirVehicleBase": "model",
    "cBuildingImpBase": "mpModel",
    "cObjectiveMarkerBase": "mModel",
    "sDestroyBase": "Model",
    "sTroopBase": "mBAN_Model",
    "cGroundVehicleBase": "mpModel",
    "sPickupBase": "mModel",
    }


zoomvalues = [(0, 0.2), (1, 0.3), (1.6, 0.6), (3.4, 0.8), (5.0, 1.0)]
def calc_zoom_in_factor(current):
    zoom = 0.2
    for val, zoomfac in zoomvalues:
        if val <= current:
            zoom = zoomfac
        elif val > current:
            break

    return zoom

def calc_zoom_out_factor(current):
    zoom = -0.2
    for val, zoomfac in reversed(zoomvalues):
        if val >= current:
            pass
        elif val < current:
            zoom = zoomfac
            break
    return -zoom

""" Test for the zoom factor calculation
test = itertools.chain(range(1, 10, 1), range(10, 20, 2), range(20, 32, 3))

for num in test:
    num = num/10.0
    out = [num]
    for i in range(20):
        out.append(round(out[-1]+calc_zoom_in_factor(out[-1]), 1))
    print(out)
    reverse = [out[-1]]
    for i in range(20):
        reverse.append(round(reverse[-1]+calc_zoom_out_factor(reverse[-1]), 1))
    print(reverse, "--")
"""

def update_mapscreen(mapscreen, obj):
    if obj.type == "cMapZone":

        positions = [x for x in map(float, obj.get_attr_value("mMatrix").split(","))]

        rotation2 = degrees(atan2(positions[0], positions[2]))
        rotation = degrees(atan2(positions[8], positions[10]))

        width, height, length, unk = [x for x in map(float, obj.get_attr_value("mSize").split(","))]
        radius = float(obj.get_attr_value("mRadius"))
        mapscreen.set_metadata(obj.id,
                               {"width": width, "length": length,
                                "radius": radius, "zonetype": obj.get_attr_value("mZoneType"),
                                "angle": rotation, "angle2": rotation2})
    elif obj.has_attr("Mat"):
        positions = [x for x in map(float, obj.get_attr_value("Mat").split(","))]
        rotation2 = degrees(atan2(positions[0], positions[2]))
        rotation = degrees(atan2(positions[8], positions[10]))

        mapscreen.set_metadata(obj.id,
                               {"angle": rotation, "angle2": rotation2})


def get_position_attribute(obj):
    if obj.has_attr("Mat"):
        return "Mat"
    if obj.type == "cMapZone":
        return "mMatrix"

    return None

def bw_coords_to_image_coords(bw_x, bw_y):
    img_x = ((bw_x + (4096//2)) // 2)
    img_y = ((bw_y + (4096//2)) // 2)
    img_y = (4096//2) - img_y

    return img_x, img_y


def image_coords_to_bw_coords(img_x, img_y):
    bw_x = img_x*2 - (4096//2)
    bw_y = (4096//2) - 2*img_y

    #print(img_x, img_y, bw_x, bw_y)

    return bw_x, bw_y
"""
for ix in range(0, 2048+1, 1024):
    for iy in range(0, 2048+1, 1024):
        x, y = image_coords_to_bw_coords(ix, iy)
        print(ix, iy, x, y, bw_coords_to_image_coords(x, y))
"""



def entity_get_model(xml, entityid):
    try:
        entityobj = xml.obj_map[entityid]
        baseobj = xml.obj_map[entityobj.get_attr_value("mBase")]
        modelobj = xml.obj_map[baseobj.get_attr_value(
            MODEL_ATTR[baseobj.type]
        )]

        return modelobj.get_attr_value("mName")
    except:
        #traceback.print_exc()
        return None


def entity_get_army(xml, entityid):
    try:
        entityobj = xml.obj_map[entityid]
        baseobj = xml.obj_map[entityobj.get_attr_value("mBase")]

        return baseobj.get_attr_value("mArmy")
    except:
        #traceback.print_exc()
        return None


def entity_get_icon_type(xml, entityid):
    try:
        entityobj = xml.obj_map[entityid]
        baseobj = xml.obj_map[entityobj.get_attr_value("mBase")]

        return baseobj.get_attr_value("unitIcon")
    except:
        #traceback.print_exc()
        return None


def set_default_path(path):
    print("WRITING", path)
    try:
        with open("default_path.cfg", "wb") as f:
            f.write(bytes(path, encoding="utf-8"))
    except Exception as error:
        print("couldn't write path")
        traceback.print_exc()
        pass


def get_default_path():
    print("READING")
    try:
        with open("default_path.cfg", "rb") as f:
            path = str(f.read(), encoding="utf-8")
        return path
    except:
        return None


def object_get_position(xml, entityid):
    obj = xml.obj_map[entityid]
    matrix_name = get_position_attribute(obj)

    matr4x4 = [float(x) for x in obj.get_attr_value(matrix_name).split(",")]
    angle = degrees(atan2(matr4x4[8], matr4x4[10]))

    x, y = matr4x4[12], matr4x4[14]

    return x, y, angle


def object_set_position(xml, entityid, x, y, angle=None):
    obj = xml.obj_map[entityid]
    matrix_name = get_position_attribute(obj)

    matr4x4 = [float(x) for x in obj.get_attr_value(matrix_name).split(",")]
    matr4x4[12] = x
    matr4x4[14] = y

    if angle is not None:
        angle2 = radians((angle+90) % 360)
        angle = radians(angle)
        matr4x4[0] = sin(angle2)
        matr4x4[2] = cos(angle2)
        matr4x4[8] = sin(angle)
        matr4x4[10] = cos(angle)


    obj.set_attr_value(matrix_name, ",".join(str(x) for x in matr4x4))


def get_type(typename):
    if typename in ("cGroundVehicle", "cTroop", "cAirVehicle", "cWaterVehicle"):
        return "a"
    else:
        return "b"

def make_gradient(start, end, step=1, max=None):
    r1, g1, b1 = start
    r2, g2, b2 = end

    diff_r, diff_g, diff_b = r2-r1, g2-g1, b2-b1
    norm = sqrt(diff_r**2 + diff_g**2 + diff_b**2)
    norm_r, norm_g, norm_b = diff_r/norm, diff_g/norm, diff_b/norm

    gradient = []
    gradient.append((int(r1), int(g1), int(b1)))

    if max is not None:
        step = int((r2-r1)/norm_r)//max

    #curr_r, curr_g, curr_b = r1, g1, b1
    for i in range(0, int((r2-r1)/norm_r), step):
        curr_r = r1+i*norm_r
        curr_g = g1+i*norm_g
        curr_b = b1+i*norm_b
        gradient.append((int(curr_r), int(curr_g), int(curr_b)))
    gradient.append((int(r2), int(g2), int(b2)))
    return gradient


def parse_terrain_to_image(terrainfile):
    # In BWii the entry at position 1 is not KNHC, but something else that needs to be skipped
    if terrainfile.entries[1].name != b"KNHC":
        off = 1
    else:
        off = 0

    tiles = terrainfile.entries[1+off] # KNHC
    #tiles2 = terrainfile.entries[4+off] # TWCU
    tilemap = terrainfile.entries[3+off]
    #tilemapdata = bytes(tilemap.data)
    pic = QImage(64*4*4, 64*4*4, QImage.Format_ARGB32)

    #colortransition = QImage(os.path.join("lib", "colors_terrainview.png"), "PNG")
    colors = []
    #for i in range(colortransition.width()):
    #    colors.append(colortransition.pixel(i, 0))
    for coltrans in [
        ((106, 199, 242), (190, 226, 241), 5),
        ((190, 226, 241), (147,182,95), 5),
        ((147,182,95), (249, 239, 160), 5),
        ((249, 239, 160), (214, 127, 70), 5),
        ((214, 127, 70), (119, 68, 39), 5),
        ((119, 68, 39), (80, 80, 80), 5),
        (((80, 80, 80), (255, 255, 255), 5))]:

        start, end, repeat = coltrans
        for color in make_gradient(start, end):
            for i in range(repeat):
                colors.append(color)
        #colors.extend([make_gradient(start, end))



    #pic = QPixmap(64*4*4, 64*4*4)
    p = QPainter()
    p.begin(pic)
    biggestheight = 0
    lowest = 0xFFFF
    print(len(tiles.data)/(180*16))
    heights = []
    for x in range(64):
        for y in range(64):
            a, b, offset = struct.unpack(">BBH", tilemap.data[(y*64+x)*4:(y*64+x+1)*4])
            #print(a,b,offset)
            if b == 1:
                tiles_data = tiles.data[180*16*offset:180*16*(offset+1)]

                for ix in range(4):
                    for iy in range(4):
                        coord_offset = iy*4+ix
                        single_tile = tiles_data[180*(coord_offset):180*(coord_offset+1)]
                        if len(single_tile) == 0:
                            print("Ooops:", offset)
                        for iix in range(4):
                            for iiy in range(4):
                                point_offset = iiy*4 + iix
                                #print("do stuff", (y*64+x)*4)
                                height = struct.unpack(">H", single_tile[point_offset*2:(point_offset+1)*2])[0]
                                pen = p.pen()
                                """if height > biggestheight:
                                    biggestheight = height
                                if height < lowest:
                                    lowest = height
                                if height not in heights:
                                    heights.append(height)
                                if height >= 0x4FF:
                                    height -= 0x4FF
                                    pen.setColor(QColor(((height>>2)+50)&0xFF, ((height>>2)+50)&0xFF, ((height>>2)+50)&0xFF))
                                elif height >= 0x3F0:
                                    height -= 0x3F0
                                    pen.setColor(QColor(((height>>2)+90)&0xFF, ((height>>2)+30)&0xFF, ((height>>2)+30)&0xFF))
                                elif height >= 0x1FF:
                                    height -= 0x1FF
                                    pen.setColor(QColor(0, ((height>>2)+30)&0xFF, 0))
                                else:
                                    pen.setColor(QColor(0, 0, ((height>>2)+30)&0xFF))"""
                                if height >= len(colors):

                                    print("oops, color out of bounds:", height, len(colors))
                                    height = len(colors)-1

                                r, g, b = colors[height]
                                pen.setColor(QColor(r, g, b))
                                #pen.setColor(QColor(height>>8, height&0xFF, height&0xFF))
                                p.setPen(pen)
                                p.drawPoint(x*16+ix*4+iix, y*16+iy*4+iiy)
    p.end()
    print(pic.size().height(), pic.size().width())
    print(biggestheight, hex(biggestheight))
    print(lowest, hex(lowest))
    heights.sort()
    print(heights)
    """p.begin(self.terrainview)
    p.drawImage(0, 0, pic)
    p.end()"""

    return pic.mirrored(False, True)
