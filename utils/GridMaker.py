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

def combine_ffx_normals():
    nm1 = Image.open("C:/Projects/ffx/images/ffx_nm_forward.combined.tga") # forward
    nm2 = Image.open("C:/Projects/ffx/images/ffx_nm_inverted.combined.tga") # inverted

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

if __name__ == "__main__":
    #rearrange_frames()
    #process_ffx("C:/Projects/ffx/images/ffx_nm_forward.{}.tga", (8, 4))
    #process_ffx("C:/Projects/ffx/images/ffx_nm_inverted.{}.tga", (8, 4))
    #combine_ffx_normals()
    process_ffx("C:/Projects/ffx/images/ffx_d.{}.tga", (8, 4))
