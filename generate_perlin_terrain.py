from math import log2, log
from PyQt5.QtGui import QImage, QPainter, QColor
from lib.opensimplex import OpenSimplex


noise = OpenSimplex(12345)

#MAX_X = 1024
#MAX_Y = 1024

MAX_X = 256
MAX_Y = 256


new = QImage(MAX_X*2, MAX_Y*2, QImage.Format_ARGB32)

trans_painter = QPainter()
trans_painter.begin(new)



def make_noise_map(noise2d, dim_x, dim_y, offsetx=0, offsety=0):
    noisemap = []
    for x in range(dim_x):
        row = []
        print("progress:", x / float(dim_x), "%")
        for y in range(dim_y):

            val = noise2d(offsetx+x, offsety+y)
            row.append(val)
        noisemap.append(row)

    return noisemap

def linear_interpolate(a1, a2, alpha):
    return a1*(1-alpha) + a2 * alpha
"""
def cubic_interpolate(x, p0, p1, p2, p3):
    #return p1 + 0.5 * x*(p2 - p0 + x*(2.0*p0 - 5.0*p1 + 4.0*p2 - p3 + x*(3.0*(p1 - p2) + p3 - p0)))
    a0 = p3 - p2 - p0 + p1
    a1 = p0 - p1 - p0
    a2 = p2 - p0
    a3 = p1

    return a0*x*x*x+a1*x*x+a2*x+a3
"""

def cubic_interpolate(t, A, B, C, D):

    a = -A / 2.0 + (3.0*B) / 2.0 - (3.0*C) / 2.0 + D / 2.0
    b = A - (5.0*B) / 2.0 + 2.0*C - D / 2.0
    c = -A / 2.0 + C / 2.0
    d = B

    return a*t*t*t + b*t*t + c*t + d

"""
def bicubic_interpolate(x, y, row1, row2, row3, row4):
    p1 = cubic_interpolate(y, *row1)
    p2 = cubic_interpolate(y, *row2)
    p3 = cubic_interpolate(y, *row3)
    p4 = cubic_interpolate(y, *row4)

    return cubic_interpolate(x, p1, p2, p3, p4)
"""

def bicubic_interpolate_noise(noisemap, factor):
    size_x = len(noisemap)
    size_y = len(noisemap[0])
    print(size_x, size_y, factor)
    print("final size will be", size_y*factor, size_x*factor)
    newnoise = [[None for y in range(size_y*factor)] for x in range(size_x*factor)]


    #for x, y in ((0, 0), (0, size_y - 4), (size_x-4, 0), (size_x-4, size_y-4)):
    for x in range(0, size_x, 2):
        for y in range(0, size_y, 2):

            x_start = x // 4
            y_start = y // 4

            for ix in range(2):
                for iy in range(2):
                    row1 = [noisemap[(x+ix-1)%size_x][(y+iy-1)%size_y], noisemap[(x+ix)%size_x][(y+iy-1)%size_y],
                            noisemap[(x+ix+1)%size_x][(y+iy-1)%size_y], noisemap[(x+ix+2)%size_x][(y+iy-1)%size_y]]

                    row2 = [noisemap[(x+ix-1)%size_x][(y+iy)%size_y], noisemap[(x+ix)%size_x][(y+iy)%size_y],
                            noisemap[(x+ix+1)%size_x][(y+iy)%size_y], noisemap[(x+ix+2)%size_x][(y+iy)%size_y]]

                    row3 = [noisemap[(x+ix-1)%size_x][(y+iy+1)%size_y], noisemap[(x+ix)%size_x][(y+iy+1)%size_y],
                            noisemap[(x+ix+1)%size_x][(y+iy+1)%size_y], noisemap[(x+ix+2)%size_x][(y+iy+1)%size_y]]

                    row4 = [noisemap[(x+ix-1)%size_x][(y+iy+2)%size_y], noisemap[(x+ix)%size_x][(y+iy+2)%size_y],
                            noisemap[(x+ix+1)%size_x][(y+iy+2)%size_y], noisemap[(x+ix+2)%size_x][(y+iy+2)%size_y]]


                    for iix in range(factor):
                        for iiy in range(factor):
                            mini_x = iix / float(factor)
                            mini_y = iiy / float(factor)
                            if x*factor+ix*factor+iix < size_x*factor and y*factor+iy*factor+iiy < size_y*factor:
                                #val = bicubic_interpolate(mini_x, mini_y, row1, row2, row3, row4)
                                val1 = cubic_interpolate(mini_x, *row1)
                                val2 = cubic_interpolate(mini_x, *row2)
                                val3 = cubic_interpolate(mini_x, *row3)
                                val4 = cubic_interpolate(mini_x, *row4)

                                val = cubic_interpolate(mini_y, val1, val2, val3, val4)

                                newnoise[x*factor+ix*factor+iix][y*factor+iy*factor+iiy] = val
    return newnoise



def billinear_interpolate_noise(noisemap, factor):
    newnoise = []

    size_x = len(noisemap)
    size_y = len(noisemap[0])

    for x in range(size_x):
        row = []
        for y in range(size_y):
            for i in range(factor):
                if y == size_y - 1:
                    start, end = noisemap[x][y], noisemap[x][0]
                else:
                    start, end = noisemap[x][y], noisemap[x][y+1]

                val = linear_interpolate(start, end, i/float(factor))
                row.append(val)

        newnoise.append(row)

    newnoise2 = []

    for y in range(size_y*factor):
        row = []
        for x in range(size_x):

            for i in range(factor):
                #print(x, y, len(newnoise), len(newnoise[x]))
                if x == size_x-1:
                    start, end = newnoise[x][y], newnoise[0][y]
                else:
                    start, end = newnoise[x][y], newnoise[x+1][y]
                val = linear_interpolate(start, end,  i/float(factor))
                row.append(val)
        newnoise2.append(row)

    fliparound = []
    for x in range(size_x*factor):
        row = []
        for y in range(size_y*factor):
            row.append(newnoise2[y][x])
        fliparound.append(row)


    return fliparound



def sample_lowres(noisemap, factor):
    newnoise = []

    size_x = len(noisemap)
    size_y = len(noisemap[0])

    for x in range(0, size_x, factor):
        row = []
        for y in range(0, size_y, factor):
            row.append(noisemap[x][y])
        newnoise.append(row)

    return newnoise




#small_noise = make_noise_map(noise.noise2d, 64, 64)
#medium_noise = make_noise_map(noise, 256, 256)# #

noisemap = make_noise_map(noise.noise2d, MAX_X, MAX_Y)
biomemap = make_noise_map(noise.noise2d, MAX_X, MAX_Y)
noise2d = noise.noise2d

print("main map generated")
"""
noisemap_2 = billinear_interpolate_noise(sample_lowres(noisemap, 2), 2)
noisemap_4 = billinear_interpolate_noise(sample_lowres(noisemap, 4), 4)
noisemap_8 = billinear_interpolate_noise(sample_lowres(noisemap, 8), 8)
noisemap_16 = billinear_interpolate_noise(sample_lowres(noisemap, 16), 16)
noisemap_32 = billinear_interpolate_noise(sample_lowres(noisemap, 32), 32)
noisemap_64 = billinear_interpolate_noise(sample_lowres(noisemap, 64), 64)
noisemap_128 = billinear_interpolate_noise(sample_lowres(noisemap, 128), 128)"""

noisemap_2 = bicubic_interpolate_noise(sample_lowres(noisemap, 2), 2)
noisemap_4 = bicubic_interpolate_noise(sample_lowres(noisemap, 4), 4)
noisemap_8 = bicubic_interpolate_noise(sample_lowres(noisemap, 8), 8)
noisemap_16 = bicubic_interpolate_noise(sample_lowres(noisemap, 16), 16)
noisemap_32 = bicubic_interpolate_noise(sample_lowres(noisemap, 32), 32)
noisemap_64 = bicubic_interpolate_noise(sample_lowres(noisemap, 64), 64)
#noisemap_128 = bicubic_interpolate_noise(sample_lowres(noisemap, 128), 128)


biomemap_low = [None for n in range(5)]
for i in range(1, 5):
    biomemap_low[i] =bicubic_interpolate_noise(sample_lowres(noisemap, 2**i), 2**i)



print("small maps generated")


def draw_height(x, y, height):
    r = g = b = height
    pen = trans_painter.pen()
    pen.setColor(QColor(r, g, b))
    trans_painter.setPen(pen)

    trans_painter.drawPoint(x, y)

STARTX = MAX_X
STARTY = MAX_Y*2

# Works
"""biomes = {#"normal": (1/32.0, 1/32.0, 1/16.0, 1/8.0, 1/16.0, 1/32.0, 1/32.0, 1/64.0),
          "normal": (1/64.0, 1/64.0, 1/16.0, 1/8.0, 1/8.0, 1/16.0, 1/8.0, 1/8.0),

          "special": (1/32.0, 1/32.0, 1/64.0, 1/32.0, 1/64.0, 1/32.0, 1/64.0, 1/128.0)}
"""
#biomes = {
#          "normal": (1/64.0, 1/64.0, 1/16.0, 1/8.0, 1/8.0, 1/16.0, 1/8.0),#, 1/8.0),
#
#          "special": (1/128.0, 1/128.0, 1/96.0, 1/64.0, 1/64.0, 1/32.0, 1/64.0)}#, 1/128.0)}


biomes = {
    "normal": (1/64.0, 1/64.0, 1/16.0, 1/8.0, 1/8.0, 1/16.0, 1/8.0),#, 1/8.0),

    "special": (1/128.0, 1/128.0, 1/96.0, 1/64.0, 1/32.0, 1/32.0, 1/64.0)}#, 1/128.0)}


for x in range(MAX_X-1, 0, -1):
    print("progress:", x / float(MAX_X), "%")
    for y in range(MAX_Y-1, 0, -1):

        #mini_noise = make_noise_map(noise2d, 3, 3, x*3, y*3)
                #if x >= len(noisemap[0]):
                #    val = 255
                #elif y >= len(noisemap):
                #    val = 255
                #else:
                #    #print(x,y, len(noisemap[0]), len(noisemap))
                biome_val = ((1/32.0)*biomemap[x][y] + (1/16.0)*biomemap_low[1][x][y]+ biomemap_low[2][x][y] +
                             biomemap_low[3][x][y] + biomemap_low[4][x][y])


                if biome_val < -0.5:
                    mode = "special"
                else:
                    mode = "normal"
                val = 0

                for mult, value in zip(biomes[mode], (
                        noisemap[x][y], noisemap_2[x][y], noisemap_4[x][y],
                        noisemap_8[x][y], noisemap_16[x][y], noisemap_32[x][y],
                        noisemap_64[x][y]#, noisemap_128[x][y]
                )):
                    val += mult*value
                #val = noisemap_32[x][y]

                """
                val = ((1/64.0)*noisemap[x][y]
                       + (1/64.0)*noisemap_2[x][y]
                       + (1/16.0)*noisemap_4[x][y]
                       + (1/8.0)*noisemap_8[x][y]
                       + (1/8.0)*noisemap_16[x][y]
                       + (1/16.0)*noisemap_32[x][y]
                       + (1/8.0)*noisemap_64[x][y]
                       + (1/8.0)*noisemap_128[x][y])
                """
                val += 1
                #print(val)
                #if val < 1.0:
                #    val = val**1.5
                #else:
                #    val = val**0.9

                #val = val**1.4
                #print(val)
                height = 16 + (val)*64

                if height < 0: height = 0

                #newx = STARTX - x + y*0.5
                #newy = STARTY - x*0.5 - y + height-50


                #draw_height(x, y, height)

                #height = 256 - height
                for i in range(int(height)-10, int(height)):
                    newx = STARTX - x + y*0.5
                    newy = STARTY - x*0.5 - y - i-30

                    #draw_height(x, y, height)
                    draw_height(newx, newy, i)
                    draw_height(newx, newy+1, i)
                    draw_height(newx-1, newy, i*0.7)

new.save("noise.png", "PNG")
