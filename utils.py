"""
This module contains a range of image manipulation functions.
Those include image segmentation, 
Every manipulation gets applied to car_edited.jpg and and saved under car_edited.jpg as well
"""
from PIL import Image

PATH_TO_EDITED = "static/images/car_edited.png"
PATH_TO_ORIGINAL = "static/images/car.png"

def read_image():
    return Image.open(PATH_TO_EDITED)

def revert_edited_image():
    """
    This method "undoes" all the modifaction applied to the image by simply replacing the edited image
    with the original image stored at 'static/images/car.jpg'
    """
    original_image = Image.open(PATH_TO_ORIGINAL)
    original_image.save(PATH_TO_EDITED)

def bw_filter():
    im = read_image()
    pixels = im.getdata()
    pixels = [3 * (int(0.299 * pixel[0] + 0.587 * pixel[1] + 0.114 * pixel[2]),) for pixel in pixels]
    im.putdata(pixels)
    return im

def sepia_pixel(p):
   # tint shadows
   if p[0] < 63:
       r,g,b = int(p[0] * 1.1), p[1], int(p[2] * 0.9)

   # tint midtones
   elif p[0] > 62 and p[0] < 192:
       r,g,b = int(p[0] * 1.15), p[1], int(p[2] * 0.85)

   # tint highlights
   else:
       r = int(p[0] * 1.08)
       g,b = p[1], int(p[2] * 0.5)
      
   return r, g, b

def sepia_filter():
    im = read_image()
    pixels = im.getdata()
    pixels = [sepia_pixel(pixel) for pixel in pixels]
    im.putdata(pixels)
    return im

def negative_filter():
    im = read_image()
    pixels = im.getdata()
    pixels = [(255 - pixel[0], 255 - pixel[1], 255 - pixel[2]) for pixel in pixels]
    im.putdata(pixels)
    return im

filters = {
    "bw": bw_filter,
    "sepia": sepia_filter,
    "negative": negative_filter
}

def apply_filter(filter, intensity):
    """
    This method edits the image by applying one of the possible filters.
    
    Parameters:
        filter (string): One of "bw", "sepia", "negative"
        intensity (float): In the range 0-1 describing how intense the applied filter should be
    """
    print("doing it")
    original_edited_im = read_image()
    edited_im = filters[filter]()

    old_pixels = original_edited_im.getdata()
    new_pixels = edited_im.getdata()

    old_intensity = 1 - intensity
    combined_pixels = [
        (
            int(old_pixel[0] * old_intensity + new_pixel[0] * intensity),
            int(old_pixel[1] * old_intensity + new_pixel[1] * intensity),
            int(old_pixel[2] * old_intensity + new_pixel[2] * intensity)
         ) for old_pixel, new_pixel in zip(old_pixels, new_pixels)
    ]
    edited_im.putdata(combined_pixels)
    edited_im.save(PATH_TO_EDITED)


