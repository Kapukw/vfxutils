from PIL import Image, ImageOps, ImageChops

frame_size = (256, 256)
grid_size = (8, 8)

out_grid_size = (grid_size[0] * frame_size[0], grid_size[1] * frame_size[1])

out_grid = Image.new('RGBA', out_grid_size)
out_nm_grid = Image.new('RGBA', out_grid_size)
background_nm_grid = Image.new('RGB', out_grid_size)
alpha_mult_grid = Image.new('L', out_grid_size)

x = 0
y = 0
for frameIdx in xrange(0, grid_size[0] * grid_size[1]):

    frame = Image.open("C:/Projects/pfx/images/test2.{}.png".format(str(10+frameIdx).zfill(4)))
    frame.thumbnail(frame_size)

    frame_nm = Image.open("C:/Projects/pfx/images/test2.PhoenixFD_normals.{}.png".format(str(10+frameIdx).zfill(4)))
    frame_nm.thumbnail(frame_size)

    background_nm = Image.open("C:/Projects/vfxutils/textures/background_nm.tga")
    background_nm.thumbnail(frame_size)

    alpha_mult = Image.open("C:/Projects/vfxutils/textures/alpha_mask.tga")
    alpha_mult.thumbnail(frame_size)

    location = (x * frame_size[0], y * frame_size[1])

    out_grid.paste(frame, location)
    out_nm_grid.paste(frame_nm, location)
    background_nm_grid.paste(background_nm, location)
    alpha_mult_grid.paste(alpha_mult, location)

    x += 1
    if x >= grid_size[0]:
        x = 0
        y += 1

# Invert normal.x 
r, g, b, a = out_nm_grid.split()
r = ImageOps.invert(r)

# Make smooth borders
a = ImageChops.multiply(a, alpha_mult_grid)

# Add smooth backgound to invisible parts for good encoding
nm_rgb_grid = ImageChops.composite(Image.merge("RGB", (r, g, b)), background_nm_grid, a)
r, g, b = nm_rgb_grid.split()
out_nm_grid = Image.merge("RGBA", (r, g, b, a))

out_nm_grid.save("y:/art/source/particles/textures/special/anim_test2_nm.tga")

# Make smooth borders
r, g, b, a = out_grid.split()
a = ImageChops.multiply(a, alpha_mult_grid)
out_grid = Image.merge("RGBA", (r, g, b, a))

out_grid.save("y:/art/source/particles/textures/special/anim_test2.tga")