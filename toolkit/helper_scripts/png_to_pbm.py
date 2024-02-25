#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from PIL import Image

def convert_to_pbm(input_png_path, output_pbm_path, width, height):
    # Open the PNG image
    png_image = Image.open(input_png_path)

    # Resize the image to the desired size
    resized_image = png_image.resize((width, height))

    # Convert the image to monochrome (1-bit) format
    monochrome_image = resized_image.convert('1')

    # Save the monochrome image as PBM format
    monochrome_image.save(output_pbm_path, format='PPM')

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python script.py <input_png_path> <output_pbm_path> <width> <height>")
        sys.exit(1)

    input_png_path = sys.argv[1]
    output_pbm_path = sys.argv[2]
    width = int(sys.argv[3])
    height = int(sys.argv[4])
    convert_to_pbm(input_png_path, output_pbm_path, width, height)

