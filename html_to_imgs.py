#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from PIL import Image, ImageOps
from io import BytesIO
import glob
import os
import numpy as np
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description='Parse the html quiz into question images.')
    parser.add_argument('html_file_path', help='Path to the html quiz.')
    parser.add_argument('--output_dir', required=True,
                        help='Output path for the generated question images.')
    args = parser.parse_args()
    return args


def setup_web(html_path):
    chrome_options = Options() # 啟動無頭模式
    chrome_options.add_argument('headless')  #規避google bug
    chrome_options.add_argument('disable-gpu')

    executable_path = '/opt/google/chrome/google-chrome'
    driver = webdriver.Chrome(executable_path='./chromedriver', options=chrome_options)

    html_file = os.path.abspath(html_path)
    driver.get("file:///" + html_file)
    return driver
                        
def remove_img(image_dir_path):
    files = glob.glob(os.path.join(image_dir_path, '*.png'))
    for f in files:
        os.remove(f)
    return

def img_file_name(image_dir_path, question_id):
    return os.path.join(image_dir_path, str(question_id).zfill(5) + '.png')

def get_crop_list(questions):
    crop_list = []
    for question in questions:
        size = question.size
        location = question.location
        # print(location)

        top = location['y']
        bottom = top + size['height']
        crop_list.append([top, bottom])
        # print(crop_list[-1])
    return crop_list

def crop_margin(img):
    ivt_image = ImageOps.invert(img.convert('RGB'))
    bbox = ivt_image.getbbox()
    cropped_image = img.crop(bbox)
    return cropped_image

def crop_save(output_dir, img_base, crop_list, body_left, body_width):
    for index, box in enumerate(crop_list):
        im = img_base.crop((body_left, box[0], body_left + body_width, box[1]))
        im = crop_margin(im)
        count_black = np.count_nonzero(np.array(im) == 0)
        im.save(img_file_name(output_dir, index))
    return

if __name__ == '__main__':
    args = parse_args()
    driver = setup_web(args.html_file_path)
    if not os.path.exists(args.output_dir):
        os.mkdir(os.path.abspath(os.path.join('.', args.output_dir)))
    remove_img(args.output_dir)

    # get body boundary
    body = driver.find_elements_by_tag_name("body")[0]
    body_left = body.location['x']
    body_width = body.size['width']
    body_top = body.location['y']
    body_height = body.size['height']

    # maximize the window size
    driver.set_window_size(body_left + body_width, body_top + body_height)

    questions = driver.find_elements_by_class_name('question') # find each question

    crop_list = get_crop_list(questions) # get each question location

    last_crop_bottom = crop_list[-1][1]

    # adjust window size to prevent bottom being hidden
    driver.set_window_size(body_left + body_width, last_crop_bottom)

    png = driver.get_screenshot_as_png()  # saves screenshot of entire page
    img_base = Image.open(BytesIO(png))  # uses PIL library to open image in memory

    # crop from base image and save png
    crop_save(args.output_dir, img_base, crop_list, body_left, body_width)

    driver.quit()
