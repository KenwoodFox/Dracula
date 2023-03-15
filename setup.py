#!/usr/bin/env python

from setuptools import setup, find_packages

readme = open("README.md").read()

setup(
    name="dracula",
    description="todo",
    author="Joe",
    author_email="31870999+KenwoodFox@users.noreply.github.com",
    url="https://github.com/KenwoodFox/dracula",
    packages=find_packages(include=["dracula"]),
    package_dir={"dracula": "dracula"},
    entry_points={
        "console_scripts": [
            "dracula=dracula.__main__:main",
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
