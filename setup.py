import os

from setuptools import find_packages, setup
from os import path

# Declare your non-python data files:
# Files underneath configuration/ will be copied into the build preserving the
# subdirectory structure if they exist.

here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

def read_requirements(path):
    with open(path, "r") as f:
        requirements = [line for line in f.readlines()]
    return requirements

setup(
    # include data files
    name="amazon-textract-textractor",
    version="0.0.2",
    description="A package to support the use of AWS Textract services.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    keywords="amazon textract aws ocr document",
    packages=find_packages(
        include=[
            "textractor.*",
            "validate.*",
            "data.*",
            "entities.*",
            "parsers.*",
            "visualizers.*",
            "utils.*",
        ],
        exclude=["docs", "tests"],
    ),
    extras_require={
        f.split(".")[0]:read_requirements(os.path.join(here, "extras", f))
        for f in os.listdir(os.path.join(here, "extras"))
    }
)