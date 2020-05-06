# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['aiodl']

package_data = \
{'': ['*']}

install_requires = \
['aiohttp>=3.6,<4.0',
 'asyncio>=3.4,<4.0',
 'numpy>=1.18,<2.0',
 'pandas>=0.25.3,<0.26.0',
 'pillow>=6.2,<7.0',
 'tqdm>=4.41,<5.0']

entry_points = \
{'console_scripts': ['aiodl = aiodl.download_img:main']}

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
