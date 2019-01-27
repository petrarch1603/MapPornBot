"""App to take a collection of 9 images and turn them into a grid collage"""

from datetime import datetime, timedelta
import io
import os
from PIL import Image, ImageDraw, ImageFont
import requests
from typing import List
from urllib.parse import urlparse

foreground = Image.open("img/grid.png")


def get_file_name(url: str) -> str:
    """Get the base filename from a URL

    :param url:
    :type url: str
    :return: base filename
    :rtype: str

    """

    path = urlparse(url).path
    return os.path.basename(path)


def get_images(url_list: list) -> list:
    """Get a list of cropped image objects

    :param url_list:List of URL's
    :type url_list: list of strings
    :return: List of 9 cropped image objects
    :rtype: list

    """

    cropped_images = []
    for i in url_list:
            url = i
            image_req = requests.get(url)

            if image_req.status_code == 200:
                my_image = Image.open(io.BytesIO(image_req.content))
                cropped_images.append(crop_image(my_image))
            if len(cropped_images) == 9:
                break
    return cropped_images


def crop_image(image_obj: object) -> object:  # Images should be 366 X 366
    """Crop images to 366 x 366 pixels

        This is the proper size for filling each grid

    :param image_obj: Image object
    :type image_obj: object
    :return: cropped Image object
    :rtype: object

    """

    ratio = image_obj.size[0] / image_obj.size[1]
    resize_tup = (int(500*ratio), 500)
    resized_img = image_obj.resize(resize_tup)
    left_edge = int((resized_img.size[0]/2) - 183)
    crop_box = (left_edge, 67, left_edge+366, 433)
    return resized_img.crop(crop_box)


def add_text(image_obj: object, contest_month: str) -> object:
    """Add text on top of image

    Centers text at Height 700. Text is a dynamic: different for each month or can be "Best of..." for
    end of year voting posts.

    :param image_obj: Image object that is being changed
    :type image_obj: object
    :param contest_month: Custom text usually the format: "November 2018" etc.
    :type contest_month: str
    :return: Image Object with text on top
    :rtype: object

    """

    font = ImageFont.truetype("fonts/Caudex-Bold.ttf", 145)
    draw = ImageDraw.Draw(image_obj)
    w, h = draw.textsize(contest_month, font=font)
    draw.text(((1150-w)/2, 700), contest_month, fill="black", font=font)
    return image_obj


def create_grid(url_list: List[str], text_content: str = '') -> str:
    """ Main function to turn list of URL strings into a contest advertisement image

    :param url_list: list of URL's (strings)
    :type url_list: list
    :param text_content: optional text content, if blank, script will add in current month and year.
    :type text_content: str
    :return: filepath
    :rtype: str

    """

    if len(url_list) < 9:
        raise Exception
    my_cropped_list = get_images(url_list)
    assert(len(my_cropped_list)) == 9
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
    if text_content == '':
        text_content = (datetime.now() - timedelta(days=7)).strftime("%B") + " " + datetime.now().strftime("%Y")
    final_image = add_text(background, text_content)
    filepath = "voteimages/" + str(datetime.now().year) + str(datetime.now().month) + "votenow.png"
    final_image.save(filepath, "PNG")
    return filepath
