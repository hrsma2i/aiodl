#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from argparse import RawTextHelpFormatter
import asyncio
from datetime import datetime
import os
import sys

import aiohttp
import numpy as np
import pandas as pd
from PIL import Image
from tqdm import tqdm


def main():
    parser = argparse.ArgumentParser(
        formatter_class=RawTextHelpFormatter)
    parser.add_argument(
        "url_file",
        help="""a csv file where urls are listed.
e.g.,

http://example/0000001.jpg
http://example/0000002.jpg
http://example/0000003.jpg

or two columns

<urls>,                    <out filenames>

http://example/0000001.jpg,out-name-001.jpg
http://example/0000002.jpg,out-name-002.jpg
http://example/0000003.jpg,out-name-003.jpg

If you doesn't designate out filenames,
the basename of urls are used as their filenames.
"""
    )
    parser.add_argument(
        "-o", "--out_dir",
        default='./download-{}'.format(
            datetime.now().strftime('%s')),
    )
    parser.add_argument(
        "-e", "--error_url_file",
        default='./error_urls-{}.csv'.format(
            datetime.now().strftime('%s')),
    )
    parser.add_argument(
        "-d", "--delimiter",
        default=',',
    )
    parser.add_argument(
        "-r", "--n_requests",
        type=int,
        default=100,
    )
    parser.add_argument(
        "-t", "--timeout",
        type=int,
        default=180,
        help="The unit is second."
    )
    parser.add_argument(
        "-c", "--check_image",
        action='store_true',
        help="""If this is True, simultaneously check
whether downloaded images are valid or not,
but it takes more time.
""",
    )
    parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="force to overwrite"
    )
    args = parser.parse_args()

    download_files(**vars(args))


def download_files(
        url_file, out_dir, error_url_file, delimiter,
        n_requests, timeout, check_image, force):

    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    else:
        if not force:
            overwrite = input(
                '{} already exists. Overwite? [y/n]: '.
                format(out_dir)) in ['y', 'yes']
            if not overwrite:
                print('Canceled.')
                sys.exit()

    df = pd.read_csv(url_file, header=None, sep=delimiter)

    urls = df[0].tolist()

    if len(df.columns) == 1:
        out_names = [os.path.basename(url) for url in urls]
    else:
        out_names = df[1].tolist()

    # avoid to many requests(coros) the same time.
    # limit them by setting semaphores (simultaneous requests)
    sem = asyncio.Semaphore(n_requests)

    coros = [
        download_file(
            url, out_dir, out_name, error_url_file,
            sem, timeout, check_image)
        for url, out_name in zip(urls, out_names)]
    eloop = asyncio.get_event_loop()
    # eloop.run_until_complete(asyncio.wait(coros))
    eloop.run_until_complete(wait_with_progressbar(coros))
    eloop.close()


async def download_file(
        url, out_dir, out_name, error_url_file,
        sem, timeout, check_image):
    # this routine is protected by a semaphore
    with await sem:
        timeout_ = aiohttp.ClientTimeout(total=timeout)
        content = await get(
            url, out_name, error_url_file,
            timeout=timeout_)
        out_file = os.path.join(out_dir, out_name)

        if content is not None:
            write_to_file(out_file, content)
            if check_image:
                await _check_img(out_file, url, out_name, error_url_file)
        # else:
        #     e = 'Response is None'
        #     tqdm.write('{}: {}'.format(out_name, e))
        #     with open(error_url_file, 'a') as f:
        #         f.write('{},{},{}\n'.format(url, out_name, e))


async def get(url, out_name, error_url_file, *args, **kwargs):
    """a helper coroutine to perform GET requests:
    """
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, *args, **kwargs) as res:
                tqdm.write('{}: {}'.format(out_name, res.status))
                return await res.content.read()
        except Exception as e:
            tqdm.write('{}: {}'.format(out_name, e))
            with open(error_url_file, 'a') as f:
                f.write('{},{},{}\n'.format(url, out_name, e))
            return None


def write_to_file(out_file, content):
    """ get content and write it to file

    Args:
        out_file ([type]): [description]
        content ([type]): [description]
    """

    with open(out_file, 'wb') as f:
        f.write(content)


async def _check_img(img_file, url, img_name, error_url_file):
    try:
        _ = await read_img(img_file)
    except Exception as e:
        tqdm.write('{}: {}'.format(img_name, e))
        with open(error_url_file, 'a') as f:
            f.write('{},{},{}\n'.format(url, img_name, e))


async def read_img(img_file):
    pil_img = Image.open(img_file).convert('RGB')
    img = np.array(pil_img).astype(np.float32)
    # (3, h, w) <- (h, w, 3)
    img = img.transpose(2, 0, 1)

    return img


async def wait_with_progressbar(coros):
    '''
    make nice progressbar
    install it by using `pip install tqdm`
    '''
    coros = [await f
             for f in tqdm(asyncio.as_completed(coros), total=len(coros))]
    return coros


if __name__ == "__main__":
    main()
