#!/usr/bin/env python

from setuptools import setup, find_packages

readme = open("README.md").read()

setup(
    name="bacubot",
    description="A bacula to discord connector",
    author="Kitsune Scientific",
    author_email="31870999+KenwoodFox@users.noreply.github.com",
    url="https://github.com/Kitsune-Scientific/bacubot",
    packages=find_packages(include=["bacubot"]),
    package_dir={"bacubot": "bacubot"},
    entry_points={
        "console_scripts": [
            "bacubot=bacubot.__main__:main",
        ],
    },
    python_requires=">=3.10.0",
    version="0.0.0",
    long_description=readme,
    include_package_data=True,
    install_requires=[
        "discord.py",
    ],
    license="MIT",
)
