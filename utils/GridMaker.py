import sys
import math
from PIL import Image, ImageOps, ImageChops

def process_ffx(fileMask, gridSize=(8, 8), smoothBorders=False):

    frameSize = Image.open(fileMask.format(str(0).zfill(4))).size
    outImgSize = (gridSize[0] * frameSize[0], gridSize[1] * frameSize[1])

    outImg = Image.new('RGBA', outImgSize)
    alphaMultImg = Image.new('L', outImgSize)

    x = 0
    y = 0
    for frameIdx in xrange(0, gridSize[0] * gridSize[1]):

        frame = Image.open(fileMask.format(str(frameIdx).zfill(4)))
        frame.thumbnail(frameSize)

        alphaMultFrame = Image.open("C:/Projects/vfxutils/textures/alpha_mask.tga")
        alphaMultFrame.thumbnail(frameSize)

        location = (x * frameSize[0], y * frameSize[1])

        outImg.paste(frame, location)
        alphaMultImg.paste(alphaMultFrame, location)

        x += 1
        if x >= gridSize[0]:
            x = 0
            y += 1

    if smoothBorders:
        r, g, b, a = outImg.split()
        a = ImageChops.multiply(a, alphaMultImg)
        outImg = Image.merge("RGBA", (r, g, b, a))

    outImg.save(fileMask.format("combined"))

def process_ffx_loop():
    frameSize = (256, 256)
    gridSize = (8, 4)

    totalFrames = gridSize[0] * gridSize[1]
    offset = 4

    outImageSize = (gridSize[0] * frameSize[0], gridSize[1] * frameSize[1])
    outImage = Image.new('RGBA', outImageSize)
    #alphaMultImage = Image.new('L', outImageSize)

    x = 0
    y = 0
    for i in xrange(1, totalFrames + 1):

        frameIdx = i + offset

        frame = Image.open("C:/Projects/ffx/images/test2.{}.tga".format(str(frameIdx).zfill(4)))
        frame.thumbnail(frameSize)

        if i <= offset and False:
            frameIdx2 = totalFrames + i
            frame2 = Image.open("C:/Projects/ffx/images/test2.{}.tga".format(str(frameIdx2).zfill(4)))
            frame2.thumbnail(frameSize)

            _x = i
            opacity = 0.5 + 0.5 * _x / float(offset + 0.5)

            frame = Image.blend(frame2, frame, opacity)

        elif i >= totalFrames - offset and False:
            frameIdx2 = offset + 1 - (totalFrames - i)
            frame2 = Image.open("C:/Projects/ffx/images/test2.{}.tga".format(str(frameIdx2).zfill(4)))
            frame2.thumbnail(frameSize)

            _x = totalFrames - i
            opacity = 0.5 * (offset + 0.5 - _x) / float(offset + 0.5)

            frame = Image.blend(frame, frame2, opacity)

        #alphaMult = Image.open("C:/Projects/vfxutils/textures/alpha_mask.tga")
        #alphaMult.thumbnail(frameSize)

        location = (x * frameSize[0], y * frameSize[1])

        outImage.paste(frame, location)
        #alphaMultImage.paste(alphaMult, location)

        x += 1
        if x >= gridSize[0]:
            x = 0
            y += 1

    # Make smooth borders
    #r, g, b, a = outImage.split()
    #a = ImageChops.multiply(a, alphaMultImage)
    #outImage = Image.merge("RGBA", (r, g, b, a))

    outImage.save("y:/art/source/particles/textures/special/ffx_loop_test.tga")

def rearrange_frames():
    srcImg = Image.open("y:/art/source/particles/textures/fire_AAA_5.png")
    frameSize = (512, 512)
    gridSize = (8, 8)
    totalFrames = gridSize[0] * gridSize[1]

    outImageSize = (gridSize[0] * frameSize[0], gridSize[1] * frameSize[1])
    outImage = Image.new('RGBA', outImageSize)

    x = 0
    y = 0
    for i in xrange(0, totalFrames):
        left = x * frameSize[0]
        top = y * frameSize[1]
        right = (x+1) * frameSize[0]
        bottom = (y+1) * frameSize[1]
        frame = srcImg.crop((left, top, right, bottom)).rotate(90)

        location = (x * frameSize[0], y * frameSize[1])

        outImage.paste(frame, location)

        x += 1
        if x >= gridSize[0]:
            x = 0
            y += 1

        outImage.save("y:/art/source/particles/textures/fire_AAA_5.tga")

def combine_ffx_normals(fileMaskForward, fileMaskInverted):
    nm1 = Image.open(fileMaskForward.format("combined")) # forward
    nm2 = Image.open(fileMaskInverted.format("combined")) # inverted

    r, g, b, a = nm1.split()
    nm1 = Image.merge("RGB", (r, g, b))
    r, g, b, a = nm2.split()
    nm2 = Image.merge("RGB", (r, g, b))

    gray = Image.new("RGB", nm1.size, (128, 128, 128))
    white = Image.new("RGB", nm1.size, (255, 255, 255))

    h1 = ImageChops.multiply(nm1, gray)
    h2 = ImageChops.multiply(ImageChops.subtract(white, nm2), gray)
    r, g, b = ImageChops.add(h2, h1).split()

    out = Image.merge("RGBA", (r, g, b, a))
    out.save("C:/Projects/ffx/images/ffx_nm_final.tga")


def generate_cloud_nm_channel(srcImg):

    # channels
    r, g, b, a = srcImg.split()

    # helper images
    gray = Image.new('L', srcImg.size, (127))
    yellowRGB = Image.new('RGB', srcImg.size, (255, 255, 0))

    # discard 'too yellow' values
    oneMinusYellowness = ImageChops.difference(Image.merge('RGB', (r, g, b)), yellowRGB)
    yR, yG, yB = oneMinusYellowness.split()
    oneMinusYellowness = ImageChops.lighter(yR, yG)
    yellowness = ImageChops.invert(oneMinusYellowness)
    yellowness = ImageChops.lighter(yellowness, gray)
    yellowness = ImageChops.subtract(yellowness, gray)
    yellowness = ImageChops.add(yellowness, yellowness)
    #yellowness.save("Y:/art/source/particles/textures/clouds/yellowness.png")

    halfRed = ImageChops.multiply(r, gray) # 50% red
    halfGreen = ImageChops.multiply(g, gray) # 50% green

    # compose
    dstImg = ImageChops.subtract(ImageChops.add(gray, halfRed), halfGreen)
    dstImg = ImageChops.composite(gray, dstImg, yellowness)

    return dstImg


# TODO: normalize dstImg
def generate_cloud_nm(horImg, vertImg):
    r = generate_cloud_nm_channel(horImg)
    g = generate_cloud_nm_channel(vertImg)
    b = Image.new('L', horImg.size, (255))
    dstImg = Image.merge('RGB', (r, g, b))
    return dstImg


def blend_nm_pixel(v1, v2):
    v = [0.0, 0.0, 1.0]
    x1 = ( float( v1[0] ) / 255.0 ) * 2.0 - 1.0
    x2 = ( float( v2[0] ) / 255.0 ) * 2.0 - 1.0
    v[0] = x1 + x2
    y1 = ( float( v1[1] ) / 255.0 ) * 2.0 - 1.0
    y2 = ( float( v2[1] ) / 255.0 ) * 2.0 - 1.0
    v[1] = y1 + y2
    z1 = ( float( v1[2] ) / 255.0 ) * 2.0 - 1.0
    z2 = ( float( v2[2] ) / 255.0 ) * 2.0 - 1.0
    v[2] = min( z1, z2 )

    if v[2] < 0.0:
        v = [0.0, 0.0, 1.0]

    vLen = math.sqrt( v[0]*v[0] + v[1]*v[1] + v[2]*v[2] )
    if vLen > 0.0:
        v[0] /= vLen
        v[1] /= vLen
        v[2] /= vLen
    else:
        v = [0.0, 0.0, 1.0]

    p = [127, 127, 255]
    for i in range(0, 3):
        p[i] = int( ( v[i] * 0.5 + 0.5 ) * 255.1 )

    return ( p[0], p[1], p[2] )


def blend_normal_maps(srcImg, dstImg):
    srcImg = Image.merge('RGB', srcImg.split()[0:3])
    dstImg = Image.merge('RGB', dstImg.split()[0:3])

    outImg = Image.new('RGB', srcImg.size, (0, 0, 0))

    srcPixels = srcImg.load()
    dstPixels = dstImg.load()
    outPixels = outImg.load()

    for i in range(0, outImg.size[0]):
        for j in range(0, outImg.size[1]):
            p1 = srcPixels[i, j]
            p2 = dstPixels[i, j]
            outPixels[i, j] = blend_nm_pixel(p1, p2)

    return outImg


def crossfade_spline(x):
    y = math.sin(x * math.pi / 2.0)
    return y


def make_grid_frames():
    frame = Image.open("D:/Projects/StaticWater_Rend_NM/0001.png")
    flat = Image.new('RGBA', frame.size, (127, 127, 255, 255))

    frameCount = 64
    altFrameCount = 32

    for i in range(1, frameCount + 1):
        frame = Image.open("D:/Projects/StaticWater_Rend_NM/{}.png".format(str(i).zfill(4)))
        if i <= altFrameCount:
            alpha = float(i) / float(altFrameCount)
            altFrame = Image.open("D:/Projects/StaticWater_Rend_NM/{}.png".format(str(frameCount + i).zfill(4)))
            altFrame = ImageChops.blend(flat, altFrame, crossfade_spline(1.0 - alpha))
            frame = ImageChops.blend(flat, frame, crossfade_spline(alpha))
            frame = blend_normal_maps(frame, altFrame)
        #frame = Image.merge('RGB', frame.split()[0:3])
        frame = blend_normal_maps(frame, flat)
        frame.save("D:/Projects/StaticWater_Fade2/{}.png".format(str(i).zfill(4)))


def make_grid():

    frame = Image.open("D:/Projects/StaticWater_Fade2/0001.png")
    outImg = Image.new('RGB', (8 * frame.size[0], 8 * frame.size[1]))

    frameNum = 1
    for j in range(0, 8):
        for i in range(0, 8):
            frame = Image.open("D:/Projects/StaticWater_Fade2/{}.png".format(str(frameNum).zfill(4)))
            location = (i * frame.size[0], j * frame.size[1])
            outImg.paste(frame, location)
            frameNum += 1

    outImg.save("y:/art/source/particles/textures/grid2.png")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        print("{}:\n\t{}".format(__file__, cmd.replace("\n", "\n\t")))
        exec(cmd)
    else:
        make_grid_frames()
        make_grid()
        #horImg = Image.open("Y:/art/source/particles/textures/clouds/hor.png")
        #vertImg = Image.open("Y:/art/source/particles/textures/clouds/vert.png")
        #dstImg = generate_cloud_nm(horImg, vertImg)
        #dstImg.save("Y:/art/source/particles/textures/clouds/cloud_nm.png")
        #process_ffx("C:/Projects/ffx/images/ffx_d.{}.tga", (8, 4))
        #process_ffx("C:/Projects/ffx/images/ffx_nm_forward.{}.tga", (8, 4))
        #process_ffx("C:/Projects/ffx/images/ffx_nm_inverted.{}.tga", (8, 4))
        #combine_ffx_normals("C:/Projects/ffx/images/ffx_nm_forward.{}.tga", "C:/Projects/ffx/images/ffx_nm_inverted.{}.tga")
        pass
