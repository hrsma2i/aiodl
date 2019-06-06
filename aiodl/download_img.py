#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import asyncio
import os
import sys

import aiohttp
import numpy as np
from PIL import Image
from tqdm import tqdm


def write_to_file(file, content):
    """ get content and write it to file

    Args:
        file ([type]): [description]
        content ([type]): [description]
    """

    with open(file, 'wb') as f:
        f.write(content)


async def read_img(img_file):
    pil_img = Image.open(img_file).convert('RGB')
    img = np.array(pil_img).astype(np.float32)
    # (3, h, w) <- (h, w, 3)
    img = img.transpose(2, 0, 1)

    return img


async def get(*args, **kwargs):
    """a helper coroutine to perform GET requests:
    """
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(*args, **kwargs) as res:
                tqdm.write('{}'.format(res.status))
                return await res.content.read()
        except Exception as e:
            tqdm.write('{}'.format(e))
            return None


async def download_file(url, out_file, error_url_file, sem):
    # this routine is protected by a semaphore
    with await sem:
        timeout = aiohttp.ClientTimeout(total=180)
        content = await get(url, timeout=timeout)
        out_name = os.path.basename(out_file)

        if content is not None:
            write_to_file(out_file, content)
            if not await check_img(out_file):
                with open(error_url_file, 'a') as f:
                    f.write('{},{}\n'.format(url, out_name))
        else:
            tqdm.write('Download Error: {}'.format(out_name))
            with open(error_url_file, 'a') as f:
                f.write('{},{}\n'.format(url, out_name))


async def check_img(img_file):
    img_name = os.path.basename(img_file)
    try:
        _ = await read_img(img_file)
        return True
    except Exception as e:
        # import traceback
        # traceback.print_exc()
        tqdm.write(img_name+': {}'.format(e))
        return False
        # return img_name + '\n'


async def wait_with_progressbar(coros):
    '''
    make nice progressbar
    install it by using `pip install tqdm`
    '''
    coros = [await f
             for f in tqdm(asyncio.as_completed(coros), total=len(coros))]
    return coros


def download(
        url_file, out_dir, out_name_file, error_url_file,
        n_requests):

    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    else:
        overwrite = input(
            '{} already exists. Overwite? [y/n]: '.
            format(out_dir)) in ['y', 'yes']
        if not overwrite:
            print('Canceled.')
            sys.exit()

    with open(url_file) as f:
        urls = f.read().splitlines()

    if out_name_file is None:
        out_files = [
            os.path.join(
                out_dir,
                os.path.basename(url)
            ) for url in urls
        ]
    else:
        with open(out_name_file) as f:
            out_files = [
                os.path.join(out_dir, out_name)
                for out_name in f.read().splitlines()
            ]

    # avoid to many requests(coros) the same time.
    # limit them by setting semaphores (simultaneous requests)
    sem = asyncio.Semaphore(n_requests)

    coros = [download_file(url, out_file, error_url_file, sem)
             for url, out_file in zip(urls, out_files)]
    eloop = asyncio.get_event_loop()
    # eloop.run_until_complete(asyncio.wait(coros))
    eloop.run_until_complete(wait_with_progressbar(coros))
    eloop.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "url_file",
        # e.g., 
        # 
        # http://example/0000001.jpg
        # http://example/0000002.jpg
        # http://example/0000003.jpg
    )
    parser.add_argument(
        "-n", "--out_name_file",
        # e.g., 
        # 
        # 0000001.jpg
        # 0000002.jpg
        # 0000003.jpg
    )
    parser.add_argument(
        "-o", "--out_dir",
        default='./downloaded'
    )
    parser.add_argument(
        "-e", "--error_url_file",
        default='./error_urls.txt'
    )
    parser.add_argument(
        "-r", "--n_requests",
        type=int,
        default=100,
    )
    args = parser.parse_args()

    download(**vars(args))


if __name__ == "__main__":
    main()
