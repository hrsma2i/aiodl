# aiodl - Async I/O Downloader

## Usage

```
$ aiodl url_file.csv
```

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

### Error URL File

An error url file is dumped, when the `aiodl` command finished.
The format of error url files is:

```
http://example/0000001.jpg,out-name-001.jpg,Error Description
http://example/0000002.jpg,out-name-002.jpg,Error Description
http://example/0000003.jpg,out-name-003.jpg,Error Description
```

If `-t`, `--timeout` option is small,
it is possible that some images aren't downloaded.
The not downloaded images will be listed in an error url file.
You can try to download them again, using the error url file as a new `url_file.csv`.

### Check Image Health

It sometimes happens that some downloaded images are invalid.
e.g., can't read the images using a image library `PIL`.

If you take the option `-c`, `--check_image`,
`aiodl` simultaneusly check whether each downloaded image is valid.
Invalid images are also listed in an error url file.

If you use a deep leanring framework `chainer`,
you can exclude invalid data, using this error url file.
