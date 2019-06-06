from setuptools import setup, find_packages


with open('./requirements.txt') as f:
    install_requires = f.read().splitlines()

setup(
    name="samplecli",
    version="0.0.1",
    description="A small package",
    author="karakaram",
    packages=find_packages(),
    install_requires=install_requires,
    entry_points={
        "console_scripts": [
            "aiodl=aiodl.download_img:main",
        ]
    },
)
