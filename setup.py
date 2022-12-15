import os

from setuptools import find_packages, setup
from os import path

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
    version="1.0.21",
    license="Apache 2.0",
    description="A package to use AWS Textract services.",
    url="https://github.com/aws-samples/amazon-textract-textractor",
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
        exclude=["docs", "tests"],
    ),
    include_package_data=True,
    install_requires=read_requirements(os.path.join(here, "requirements.txt")),
    extras_require={
        f.split(".")[0]:read_requirements(os.path.join(here, "extras", f))
        for f in os.listdir(os.path.join(here, "extras"))
    },
    entry_points = {
        "console_scripts": [
            "textractor = textractor.cli.cli:textractor_cli",
        ],
    },
)
