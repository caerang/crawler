# Copyright 2019, Hyeongdo Lee. All Rights Reserved.
# 
# e-mail: mylovercorea@gmail.com
#
# ==============================================================================
"""
"""
import requests
import uuid
import os
from multiprocessing import Pool


def download_image(args):
    url = args[1]
    file_name = args[0]
    i = requests.get(url)

    if i.status_code == requests.codes.ok:
        with open(file_name, 'wb') as fd:
            fd.write(i.content)


def download_images(posts, tag):
    img_urls = []
    for post in posts:
        img_urls.append(post['img_url'])

    with Pool(4) as pool:
        for img_url in img_urls:
            namewfile = img_url.split('?')
            ext = os.path.splitext(namewfile[0])
            file_name = f'./data/{tag}-{uuid.uuid1().hex[:8]}{ext[1]}'
            print(file_name)
            pool.map(download_image, [(file_name, img_url)])
