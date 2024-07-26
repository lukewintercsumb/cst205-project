"""
course: CST205
title: Paint editor
abstract: This module contains a range of image manipulation functions.
          Those include image segmentation, 
          Every manipulation gets applied to car_edited.jpg and and saved under car_edited.jpg as well
authors: Elina Adibi, William Hurley, Luke Winter, Samuel Scott
date: 07-26-24
note: All the CSRF had to be added to make sure that the form work. We are not sure why that is required, but potentially it is a mac issue.
"""

from PIL import Image
import tensorflow as tf
import numpy as np
import pickle
import os
from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000

PATH_TO_SELECTION = "static/images/car_selection.png"
PATH_TO_EDITED = "static/images/car_edited.png"
PATH_TO_ORIGINAL = "static/images/car.png"
PATH_TO_MASK = "static/mask/mask.pkl"

def read_image(original=False):
    # return Image.open(PATH_TO_EDITED if not original else PATH_TO_ORIGINAL)
    if not original:
        try:
            return Image.open(PATH_TO_EDITED)
        except FileNotFoundError:
            print("Edited image not found. Creating a new edited image from the original.")
            original_image = Image.open(PATH_TO_ORIGINAL)
            original_image.save(PATH_TO_EDITED)
            return original_image
    else:
        return Image.open(PATH_TO_ORIGINAL)

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
   """
   note: The sepia_pixel method is copied directly from the lecture slides
   """
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
    """
    note: The sepia_filter method is copied directly from the lecture slides and modified only slightly
    """
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

def color_distance(color1, color2):
    """
    note: most of the code was copied from the lecture slides 'Digital Color Manipulation (Part 2)'
    """
    def patch_asscalar(a):
        return a.item()
    setattr(np, "asscalar", patch_asscalar)

    color1_rgb = sRGBColor(color1[0], color1[1], color1[2], True)
    color2_rgb = sRGBColor(color2[0], color2[1], color2[2], True)

    color1_lab = convert_color(color1_rgb, LabColor)
    color2_lab = convert_color(color2_rgb, LabColor)

    return delta_e_cie2000(color1_lab, color2_lab)

def image_segmentation(selection):
    """
    This method is used to find the car/paint in the image. 
    Parameters:
        selection (list(tuples)): Gives the selected pixels as a list of tuples
    """
    threshold = 15
    im = read_image(original=True)
    pixels = im.getdata()

    mask = []
    for pixel in pixels:
        # get the minimum distance between the current pixel and the selections
        minimum_distance = threshold + 1 # initialize to be bigger then threshold
        for selected_pixel in selection:
            distance = color_distance(selected_pixel, pixel)
            if distance < minimum_distance:
                minimum_distance = distance
        mask.append(minimum_distance <= threshold)



    os.makedirs(os.path.dirname(PATH_TO_MASK), exist_ok=True)



    # we use pickle to store the image mask
    with open(PATH_TO_MASK, "wb") as file:
        pickle.dump(mask, file)

    print(f"Mask created with {len(mask)} elements.")

    # update car_selection.jpg
    im_selection = Image.open(PATH_TO_ORIGINAL)
    im_selection_pixels = im_selection.getdata()
    new_pixels = []
    for old_selection_pixel, is_selected in zip(im_selection_pixels, mask):
        if is_selected:
            new_pixels.append(
                (
                    int((old_selection_pixel[0] * 0.2 + 255 * 0.8)),
                    old_selection_pixel[1],
                    old_selection_pixel[2]
                )
            )
        else:
            new_pixels.append(old_selection_pixel)
    im_selection.putdata(new_pixels)
    im_selection.save(PATH_TO_SELECTION)

def edit_paint(chosen_color):
    """
    1. get the current paint color (approximation as average of selections)
    2. for each selected pixel, get the vector from average paint color to that pixel.
    3. replace each selected pixel with the seleceted color, plus the priviously acquired color vector.
    """
    mask = None
    try:
        with open(PATH_TO_MASK, "rb") as file:
            mask = pickle.load(file)
    except EOFError:
        print("EOFError: The mask file is empty or corrupted.")
        return
    except FileNotFoundError:
        print("FileNotFoundError: The mask file does not exist.")
        return

    print("Mask loaded successfully.")

    im = read_image(PATH_TO_ORIGINAL)

    pixels = im.getdata()

    count = 0
    color_sums = [0, 0, 0]
    for is_paint, pixel in zip(mask, pixels):
        if is_paint and count % 10 == 0: # only look at one in ten pixels, for more efficient computation
            color_sums[0] += pixel[0]
            color_sums[1] += pixel[1]
            color_sums[2] += pixel[2]
            count += 1

    if count == 0:
        print("No pixels were selected for painting.")
        return

    average_color = [ x // count for x in color_sums]
    new_pixels = []
    for is_paint, pixel in zip(mask, pixels):
        if is_paint:
            # Calculate the color difference vector
            diff_vector = [pixel[i] - average_color[i] for i in range(3)]
            # Apply the difference to the chosen color
            new_pixel = tuple(min(max(chosen_color[i] + diff_vector[i], 0), 255) for i in range(3))
            new_pixels.append(new_pixel)
        else:
            new_pixels.append(pixel)


    im.putdata(new_pixels)
    im.save(PATH_TO_EDITED)

# image_segmentation([(199, 219, 249), (34, 140, 227), (91, 106, 133)])
# edit_paint((227, 10, 10))