#!/usr/bin/env python
# -*- coding: utf-8 -*-

from time import time
import asyncio
from datetime import datetime
from logging import getLogger, INFO, StreamHandler
from pathlib import Path
from typing import Dict

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

    downloader = Downloader(
        out_dir=out_dir, num_requests=num_requests, timeout=timeout, total=len(urls)
    )
    coros = [
        downloader.download(url, out_name) for url, out_name in zip(urls, out_names)
    ]
    eloop = asyncio.get_event_loop()
    eloop.run_until_complete(asyncio.wait(coros))
    eloop.close()


class Downloader:
    def __init__(self, out_dir: Path, num_requests: int, timeout: int, total: int):
        self.out_dir = out_dir
        # avoid to many requests(coros) the same time.
        # limit them by setting semaphores (simultaneous requests)
        self.sem = asyncio.Semaphore(num_requests)
        self.timeout_ = aiohttp.ClientTimeout(total=timeout)
        self.total = total

        self._count = 0

    @property
    def _throughput(self):
        elapsed = time() - self._start
        return self._count / elapsed

    def _log_dict(self, out_name: str, extra: Dict = {}):
        return {
            **{
                "count": self._count,
                "total": self.total,
                "throughput": self._throughput,
                "out_name": out_name,
            },
            **extra,
        }

    async def download(self, url: str, out_name: str):
        # this routine is protected by a semaphore
        if self._count == 0:
            self._start = time()

        with await self.sem:
            try:
                content = await self.get(url, out_name, timeout=self.timeout_)

                self.write(self.out_dir / out_name, content)

                self._count += 1
                logger.info(self._log_dict(out_name))
            except Exception as e:
                self._count += 1
                logger.error(self._log_dict(out_name, extra={"error": e}))

    async def get(self, url, out_name, *args, **kwargs):
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            async with session.get(url, *args, **kwargs) as res:
                return await res.content.read()

    def write(self, out_file: Path, content: bytes):
        """

        Args:
            out_file (Path): [description]
            content (bytes): [description]

        NOTE: asyncio doesn't support file I/O.
        aiofile is slower than sync file writing.
        """
        with out_file.open("wb") as f:
            f.write(content)
