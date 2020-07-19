#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
from datetime import datetime
from logging import getLogger, INFO, StreamHandler
from pathlib import Path

import aiohttp
import pandas as pd
import typer

from aiodl.log_json_formatter import CustomJsonFormatter


logger = getLogger(__name__)
logger.setLevel(INFO)

handler = StreamHandler()
formatter = CustomJsonFormatter()
handler.setFormatter(formatter)
logger.addHandler(handler)

URL_CSV_HELP = """a csv file where urls are listed.
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


def run_with_typer():
    typer.run(main)


def main(
    url_file: Path = typer.Argument(..., help=URL_CSV_HELP),
    out_dir: Path = typer.Option(
        datetime.now().strftime("download-%Y-%m-%d-%H-%M-%S"),
        "-o",
        help="Output directory",
    ),
    delimiter: str = typer.Option(",", "-d", help="Delimiter"),
    num_requests: int = typer.Option(100, "-r", help="Number of requests"),
    timeout: int = typer.Option(180, "-t", help="Timeout(sec)"),
    add: bool = typer.Option(False, "-a", help="Add files to the existing directory."),
):
    if not out_dir.is_dir():
        out_dir.mkdir(parents=True)
    else:
        if add:
            logger.info(f"add to {out_dir} that has already exists")
            pass
        else:
            raise OSError(f"out_dir={out_dir} has already exists")

    df = pd.read_csv(url_file, header=None, sep=delimiter)

    urls = df[0].tolist()

    if len(df.columns) == 1:
        out_names = [url.split("/")[-1] for url in urls]
    else:
        out_names = df[1].tolist()

    downloader = Downloader(out_dir=out_dir, num_requests=num_requests, timeout=timeout)
    coros = [
        downloader.download(url, out_name) for url, out_name in zip(urls, out_names)
    ]
    eloop = asyncio.get_event_loop()
    eloop.run_until_complete(asyncio.wait(coros))
    eloop.close()


class Downloader:
    def __init__(self, out_dir, num_requests, timeout):
        self.out_dir = out_dir
        # avoid to many requests(coros) the same time.
        # limit them by setting semaphores (simultaneous requests)
        self.sem = asyncio.Semaphore(num_requests)
        self.timeout_ = aiohttp.ClientTimeout(total=timeout)

    async def download(self, url, out_name):
        # this routine is protected by a semaphore
        with await self.sem:
            content = await self.get(url, out_name, timeout=self.timeout_)
            out_file = self.out_dir / out_name

            if content is not None:
                self.write(out_file, content)

    async def get(self, url, out_name, *args, **kwargs):
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            try:
                async with session.get(url, *args, **kwargs) as res:
                    logger.info({"out_name": out_name})
                    return await res.content.read()
            except Exception as e:
                logger.error({"out_name": out_name, "error": e})
                return None

    def write(self, out_file: Path, content: bytes):
        with out_file.open("wb") as f:
            f.write(content)
