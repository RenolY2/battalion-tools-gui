import struct

from PyQt5.QtGui import QPicture, QPainter, QImage, QColor, QPixmap

from res_tools.bw_archive_base import BWArchiveBase

SCALE = 24

CORNER_NEIGHBOURS = {
    (0, 0): ((-1,0), (-1,-1), (0,-1)),
    (0, 3): ((-1,0), (-1, 1), (0, 1)),
    (3, 3): ((1,0), (1, 1), (0,1)),
    (3, 0): ((1, 0), (1, -1), (0,-1))
}

def get_average_height(image, point_x, point_y, img_x, img_y):
    self_height = image.pixel(img_x, img_y) & 0xFF
    average = self_height
    if (point_x, point_y) in CORNER_NEIGHBOURS:
        neighbours = CORNER_NEIGHBOURS[(point_x, point_y)]
        for ix, iy in neighbours:
            height = image.pixel(img_x+ix, img_y-iy) & 0xFF
            average += height
        average = average // 4

    else:
        if point_x == 0:
            neighbour = (-1, 0)
        elif point_x == 3:
            neighbour = (1, 0)
        elif point_y == 0:
            neighbour = (0, -1)
        elif point_y == 3:
            neighbour = (0, 1)
        else:
            return self_height

        ix, iy = neighbour
        height = image.pixel(img_x+ix, img_y-iy) & 0xFF
        average = (average+height) // 2

    return average


def parse_terrain_to_image(terrainfile, waterheight=None):
    # In BWii the entry at position 1 is not KNHC, but something else that needs to be skipped
    if terrainfile.entries[1].name != b"KNHC":
        off = 1
    else:
        off = 0

    tiles = terrainfile.entries[1+off] # KNHC
    #tiles2 = terrainfile.entries[4+off] # TWCU
    tilemap = terrainfile.entries[3+off] # PAMC
    #tilemapdata = bytes(tilemap.data)
    pic = QImage(64*4*4, 64*4*4, QImage.Format_ARGB32)
    light_pic = QImage(64*4*4, 64*4*4, QImage.Format_ARGB32)

    #colortransition = QImage(os.path.join("lib", "colors_terrainview.png"), "PNG")
    #colors = []

    #for i in range(colortransition.width()):
    #    colors.append(colortransition.pixel(i, 0))

    """new = QImage(len(colors), 200, QImage.Format_ARGB32)
    trans_painter = QPainter()
    trans_painter.begin(new)
    for i in range(len(colors)):
        r, g, b = colors[i]
        pen = trans_painter.pen()
        pen.setColor(QColor(r, g, b))
        trans_painter.setPen(pen)
        for y in range(200):
            trans_painter.drawPoint(i, y)

    trans_painter.end()
    result = new.save("transition.png", "PNG")
    print("saved", result)"""
    #pic = QPixmap(64*4*4, 64*4*4)
    p = QPainter()
    p.begin(pic)
    light_p = QPainter()
    light_p.begin(light_pic)
    biggestheight = 0
    lowest = 0xFFFF
    print(len(tiles.data)/(180*16))
    heights = []
    watercolor = (106, 152, 242)

    lowest_values = {}
    total_lowest_color = None

    for x in range(64):
        for y in range(64):
            a, b, offset = struct.unpack(">BBH", tilemap.data[(y*64+x)*4:(y*64+x+1)*4])
            #print(a,b,offset)
            if b == 1:
                tiles_data = tiles.data[180*16*offset:180*16*(offset+1)]
                lowest = 0xFFFF
                lowest_color = None
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

                                light_r, light_g, light_b, unused = struct.unpack("BBBB", single_tile[32+point_offset*4:32+(point_offset+1)*4])
                                pen = p.pen()
                                r = g = b = height//SCALE

                                pen.setColor(QColor(r, g, b))
                                p.setPen(pen)
                                p.drawPoint(x*16+ix*4+iix, y*16+iy*4+iiy)
                                pen.setColor(QColor(light_r, light_g, light_b))
                                light_p.setPen(pen)
                                light_p.drawPoint(x*16+ix*4+iix, y*16+iy*4+iiy)

                lowest_values[(x, y)] = lowest_color
    p.end()
    light_p.end()


    print(pic.size().height(), pic.size().width())
    print(biggestheight, hex(biggestheight))
    print(lowest, hex(lowest))
    heights.sort()
    print(heights)

    finalimage = QImage(pic.width(), pic.height(), QImage.Format_ARGB32)
    p.begin(finalimage)


    p.drawImage(0, 0, pic)
    p.end()
    """p.begin(self.terrainview)
    p.drawImage(0, 0, pic)
    p.end()"""

    return finalimage.mirrored(False, True), light_pic.mirrored(False, True)#pic.mirrored(False, True)

def parse_image_change(image, terrainfile):
    if terrainfile.entries[1].name != b"KNHC":
        off = 1
    else:
        off = 0

    tiles = terrainfile.entries[1+off] # KNHC
    #tiles2 = terrainfile.entries[4+off] # TWCU
    tilemap = terrainfile.entries[3+off] # PAMC
    print("mmm", len(tiles.data), len(tilemap.data), len(tilemap.data)/4)

    for chunk_x in range(64):
        for chunk_y in range(64):
            chunkoffset = (chunk_y*64+chunk_x)
            a, b, offset = struct.unpack(">BBH", tilemap.data[chunkoffset*4:(chunkoffset+1)*4])
            if b == 1:
                tiles_data = tiles.data[180*16*offset:180*16*(offset+1)]
                #tiles_data[:] = b"\x00" * len(tiles_data)
                #print("what", tiles_data, len(tiles_data), offset)

                for tile_x in range(4):
                    for tile_y in range(4):
                        coord_offset = tile_y*4+tile_x
                        single_tile = tiles_data[180*(coord_offset):180*(coord_offset+1)]

                        for point_x in range(4):
                            for point_y in range(4):
                                img_x = chunk_x*16 + tile_x*4 + point_x
                                img_y = 64*4*4 - (chunk_y*16 + tile_y*4 + point_y)
                                #img_y = (chunk_y*16 + tile_y*4 + point_y)

                                height = (image.pixel(img_x, img_y)>>8) & 0xFF
                                final_height = get_average_height(image, point_x, point_y, img_x, img_y)

                                #print(type(height))
                                #print(coord_offset, single_tile, len(single_tile), type(single_tile))
                                struct.pack_into(">H", single_tile, (point_y*4+point_x)*2,
                                                 final_height*SCALE)
                                #struct.pack_into(">BBH", tilemap.data, chunkoffset*4,
                                #                 a, b, height*24)

    print("done")





if __name__ == "__main__":
    # The original terrain file you want to modify goes here
    with open("terrain/C1_OnPatrol.out", "rb") as f:
        terrain = BWArchiveBase(f)

    # Uncomment this and change the filename accordingly when using the
    # script for the first time. After that, comment it again
    #terrain_img, light_img = parse_terrain_to_image(terrain)
    #terrain_img.save("terraintest.png", "PNG")

    # The image path from above goes here
    parse_image_change(QImage("terraintest.png", "PNG"), terrain)

    # The path to the final terrain file goes here.
    with open("terrainchanged.out", "wb") as f:
        terrain.write(f)


    # This is for checking how the new terrain looks.
    with open("terrainchanged.out", "rb") as f:
        terrain_new = BWArchiveBase(f)

    terrain_img, light_img = parse_terrain_to_image(terrain_new)
    terrain_img.save("terraintest2.png", "PNG")
