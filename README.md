# aiodl - Async I/O Downloader

## Installation

```sh
$ git clone https://github.com/hrsma2i/aiodl.git
$ cd aiodl
$ pip install -e .
```

## Usage

```sh
$ aiodl url_file.csv -o downloaded_images/ 2>&1 | tee log-`date +%s`.jsonlines
```

You can use the log file to retry downloading error URLs, converting the log jsonlines to an input csv by `jq` command.

### Format of url_file.csv

The format of `url_file.csv` is:

e.g.,

```
http://example/0000001.jpg
http://example/0000002.jpg
http://example/0000003.jpg
```

or two columns

1. url
2. out filename

```
http://example/0000001.jpg,out-name-001.jpg
http://example/0000002.jpg,out-name-002.jpg
http://example/0000003.jpg,out-name-003.jpg
```

If you don't designate out filenames (single column),
the basename of urls are used as their filenames.
e.g, if the url is `http://example/0000003.jpg`, the out filename is `0000003.jpg`.
