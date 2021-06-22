import asyncio
import os
from datetime import datetime, timedelta
from logging import INFO, StreamHandler, getLogger
from pathlib import Path
from time import time
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
    max_retry: int = typer.Option(3, "-m", help="Max retry"),
    add: bool = typer.Option(False, "-a", help="Add files to the existing directory."),
    skip_exists: bool = typer.Option(
        False, "-s", help="If the file already exists, skip it."
    ),
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

    if skip_exists:

        def exist_file(row):
            return not os.path.isfile(out_dir / row[1])

        try:
            urls, out_names = list(zip(*list(filter(exist_file, zip(urls, out_names)))))
        except ValueError:
            logger.warning("There are no files to download.")
            return

    downloader = Downloader(
        out_dir=out_dir,
        num_requests=num_requests,
        timeout=timeout,
        total=len(urls),
        max_retry=max_retry,
    )
    coros = [
        downloader.download(url, out_name) for url, out_name in zip(urls, out_names)
    ]
    eloop = asyncio.get_event_loop()
    eloop.run_until_complete(asyncio.wait(coros))
    eloop.close()


class Downloader:
    def __init__(
        self, out_dir: Path, num_requests: int, timeout: int, total: int, max_retry: int
    ):
        self.out_dir = out_dir
        # avoid to many requests(coros) the same time.
        # limit them by setting semaphores (simultaneous requests)
        self.sem = asyncio.Semaphore(num_requests)
        self.timeout_ = aiohttp.ClientTimeout(total=timeout)
        self.total = total
        self.max_retry = max_retry

        self._count = 0

    def _log_dict(self, out_name: str, num_retry: int = 0, extra: Dict = {}):
        elapsed = time() - self._start
        throughput = self._count / elapsed
        d = {
            **{
                "count": self._count,
                "total": self.total,
                "progress": f"{int(self._count / self.total * 100)}%",
                "throughput": throughput,
                "out_name": out_name,
            },
            **extra,
        }

        if throughput > 0:
            d["remaining"] = str(
                timedelta(seconds=(self.total - self._count) / throughput)
            )

        if num_retry > 0:
            d["retry"] = num_retry
        return d

    async def download(self, url: str, out_name: str, num_retry: int = 0):
        # this routine is protected by a semaphore
        if self._count == 0:
            self._start = time()

        with await self.sem:
            try:
                content = await self.get(url, out_name, timeout=self.timeout_)

                self.write(self.out_dir / out_name, content)

                self._count += 1
                logger.info(self._log_dict(out_name))
            except aiohttp.ClientResponseError as e:
                if num_retry < self.max_retry and e.status not in [403]:
                    self._count += 1

                logger.error(
                    self._log_dict(
                        out_name,
                        num_retry=num_retry,
                        extra={"retry": num_retry, "error": e},
                    )
                )

                if num_retry < self.max_retry:
                    await self.download(url, out_name, num_retry + 1)
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
