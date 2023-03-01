import os
import sys
from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


requirements = ['marshmallow']

if sys.argv[-1] == 'publish-test':
    os.system(f"cd {os.path.dirname(__file__)}")
    os.system('rm -rf dist/ build/ idp-cdk-manifest.egg-info/')
    os.system('python setup.py sdist bdist_wheel')
    os.system('twine check dist/*')
    os.system('twine upload --repository pypitest dist/*')
    sys.exit()

if sys.argv[-1] == 'publish':
    os.system(f"cd {os.path.dirname(__file__)}")
    os.system('rm -rf dist/ build/ idp-cdk-manifest.egg-info/')
    os.system('python setup.py sdist bdist_wheel')
    os.system('twine check dist/*')
    os.system('twine upload --repository pypi dist/*')
    sys.exit()

setup(name='amazon-textract-idp-cdk-manifest',
      packages=find_packages(exclude=['tests']),
      include_package_data=True,
      exclude_package_data={"": ["test_*.py", "__pycache__"]},
      version='0.0.1',
      description='Amazon Textract IDP CDK Manifest',
      install_requires=requirements,
      extras_require={'testing': ['pytest']},
      long_description_content_type='text/markdown',
      long_description=read('README.md'),
      author='Amazon Rekognition Textract Demoes',
      author_email='rekognition-textract-demos@amazon.com',
      url='https://github.com/aws-samples/amazon-textract-textractor/tree/master/idp_cdk_manifest',
      keywords='textract manifest',
      license="Apache License Version 2.0",
      classifiers=[
          "Development Status :: 4 - Beta",
          "Topic :: Utilities",
          'License :: OSI Approved :: Apache Software License',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3.8',
          'Programming Language :: Python :: 3.9',
      ],
      python_requires='>=3.7')
