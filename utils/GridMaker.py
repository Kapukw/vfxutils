from PIL import Image, ImageOps

out_im = Image.new('RGBA', (2048, 2048))
out_nm = Image.new('RGBA', (2048, 2048))
out_bg_nm = Image.new('RGB', (2048, 2048))
out_alpha_mask = Image.new('RGB', (2048, 2048))

x = 0
y = 0
for frameIdx in xrange(0, 64):
    frame_im = Image.open("C:/Projects/pfx/images/test2.{}.png".format(str(10+frameIdx).zfill(4)))
    frame_nm = Image.open("C:/Projects/pfx/images/test2.PhoenixFD_normals.{}.png".format(str(10+frameIdx).zfill(4)))
    background_nm = Image.open("C:/Projects/pfx/images/background_nm.png")
    a_mask = Image.open("C:/Projects/pfx/images/alpha_mask.png")

    frame_im.thumbnail((256, 256))
    frame_nm.thumbnail((256, 256))
    background_nm.thumbnail((256, 256))
    a_mask.thumbnail((256, 256))

    out_im.paste(frame_im, (x * 256, y * 256))
    out_nm.paste(frame_nm, (x * 256, y * 256))
    out_bg_nm.paste(background_nm, (x * 256, y * 256))
    out_alpha_mask.paste(a_mask, (x * 256, y * 256))

    x += 1
    if x >=8:
        x = 0
        y += 1

r, g, b, a = out_nm.split()
r = ImageOps.invert(r)
out_nm = Image.merge("RGBA", (r, g, b, a))

out_im.save("y:/art/source/particles/textures/special/anim_test2.tif")
out_nm.save("y:/art/source/particles/textures/special/anim_test2_nm.tif")
out_bg_nm.save("y:/art/source/particles/textures/special/anim_test2_bg_nm.tif")
out_alpha_mask.save("y:/art/source/particles/textures/special/anim_test2_a_msk.tif")
a.save("y:/art/source/particles/textures/special/anim_test2_a.tif")