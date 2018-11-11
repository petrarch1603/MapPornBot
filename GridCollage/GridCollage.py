"""App to take a collection of 9 images and turn them into a grid collage"""

from datetime import datetime, timedelta
import io
import os
from PIL import Image, ImageDraw, ImageFont
import requests
from urllib.parse import urlparse

foreground = Image.open("img/grid.png")


def get_file_name(url):
    path = urlparse(url).path
    return os.path.basename(path)


def get_images(url_list):

    cropped_images = []
    for i in url_list:
        url = i
        image_req = requests.get(url)

        if image_req.status_code == 200:
            my_image = Image.open(io.BytesIO(image_req.content))
            cropped_images.append(crop_image(my_image))
    return cropped_images


def crop_image(image_obj):  # Images should be 366 X 366
    ratio = image_obj.size[0] / image_obj.size[1]
    resize_tup = (int(500*ratio), 500)
    resized_img = image_obj.resize(resize_tup)
    left_edge = int((resized_img.size[0]/2) - 183)
    crop_box = (left_edge, 67, left_edge+366, 433)
    return resized_img.crop(crop_box)


def add_text(image_obj, contest_month):

    # Each character is approximately 30 pixels
    # Therefore to adjust the text to the center, we add 30 pixels to each character
    word_length = len(contest_month)
    adjustment = int((9-word_length) * 30)

    font = ImageFont.truetype("fonts/Caudex-Bold.ttf", 145)
    draw = ImageDraw.Draw(image_obj)
    draw.multiline_text((35 + adjustment, 700),
                        text=str(contest_month + " " + datetime.now().strftime("%Y")),
                        font=font,
                        align="center",
                        fill=(0, 0, 0, 255))
    return image_obj


def main(url_list):
    my_cropped_list = get_images(url_list)
    background = Image.new('RGB', (1150, 1150))
    i = 0
    x = 0
    y = 0
    for col in range(3):
        for row in range(3):
            background.paste(my_cropped_list[i], (x, y))
            i += 1
            y += 366+25  # 25 pixels is the buffer between images
        x += 366+25
        y = 0
    background.paste(foreground, (0, 0), foreground)
    contest_month = (datetime.now() - timedelta(days=7)).strftime("%B")
    final_image = add_text(background, contest_month)
    filepath = "img/" + str(datetime.now().year) + str(datetime.now().month) + "votenow.png"
    final_image.save(filepath, "PNG")
    return filepath
