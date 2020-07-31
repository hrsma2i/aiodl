# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['aiodl']

package_data = \
{'': ['*']}

install_requires = \
['aiohttp>=3.6,<4.0',
 'asyncio>=3.4,<4.0',
 'pandas>=0.25.3,<0.26.0',
 'python-json-logger>=0.1.11,<0.2.0',
 'tqdm>=4.41,<5.0',
 'typer>=0.3.1,<0.4.0']

entry_points = \
{'console_scripts': ['aiodl = aiodl.download_img:run_with_typer']}

setup_kwargs = {
    'name': 'aiodl',
    'version': '0.1.0',
    'description': '',
    'long_description': None,
    'author': 'hrsma2i',
    'author_email': 'hrs.ma2i@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.6,<4.0',
}


setup(**setup_kwargs)
