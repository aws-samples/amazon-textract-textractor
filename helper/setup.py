import os
import sys
from setuptools import setup, find_packages
from setuptools.command.install import install


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


class FontInstaller(install):
    def run(self):
        self._copy_fonts()
        install.run(self)

    def _copy_fonts(self):
        try:
            import shutil

            if sys.platform == "win32":
                # check the windows font repository
                # NOTE: must use uppercase WINDIR, to work around bugs in
                # 1.5.2's os.environ.get()
                windir = os.environ.get("WINDIR")
                if windir:
                    tgt_dir = os.path.join(windir, "fonts")
            elif sys.platform in ("linux", "linux2"):
                lindirs = os.environ.get("XDG_DATA_DIRS", "")
                if not lindirs:
                    # According to the freedesktop spec, XDG_DATA_DIRS should
                    # default to /usr/share
                    tgt_dir = "/usr/share/fonts"
                else:
                    lindir = lindirs.split(":")[0]
                    tgt_dir = os.path.join(lindir, "fonts")
            elif sys.platform == "darwin":
                tgt_dir = os.path.expanduser("~/Library/Fonts")

            if not os.path.isdir(tgt_dir):
                print('WARNING: Could not locate fonts directory. Default font will be used')
            else:
                _src_dir = 'fonts/'
                _font_file = 'Roboto-Regular.ttf'

                if _font_file not in os.listdir(tgt_dir):
                    shutil.copyfile(os.path.join(_src_dir, _font_file), os.path.join(tgt_dir, _font_file))

        except:
            print('WARNING: An issue occured while installing the custom fonts. Default font will be used')


requirements = [
    'boto3', 'botocore', 'amazon-textract-response-parser>=0.1.27', 'amazon-textract-caller>=0.0.16',
    'amazon-textract-overlayer>=0.0.3', 'amazon-textract-prettyprinter>=0.0.10', 'Pillow>=9.1.1', 'PyPDF2==2.4.2 '
]

if sys.argv[-1] == 'publish-test':
    os.system(f"cd {os.path.dirname(__file__)}")
    os.system('rm -rf dist/ build/ amazon_textract_helper.egg-info/')
    os.system('python setup.py sdist bdist_wheel')
    os.system('twine check dist/*')
    os.system('twine upload --repository pypitest dist/*')
    sys.exit()

if sys.argv[-1] == 'publish':
    os.system(f"cd {os.path.dirname(__file__)}")
    os.system('rm -rf dist/ build/ amazon_textract_helper.egg-info/')
    os.system('python setup.py sdist bdist_wheel')
    os.system('twine check dist/*')
    os.system('twine upload --repository pypi dist/*')
    sys.exit()

setup(name='amazon-textract-helper',
      packages=find_packages(exclude=['tests']),
      include_package_data=True,
      exclude_package_data={"": ["test_*.py", "__pycache__"]},
      version='0.0.31',
      description='Amazon Textract Helper tools',
      install_requires=requirements,
      scripts=['bin/amazon-textract'],
      long_description_content_type='text/markdown',
      long_description=read('README.md'),
      author='Amazon Rekognition Textract Demoes',
      author_email='rekognition-textract-demos@amazon.com',
      url='https://github.com/aws-samples/amazon-textract-textractor/tree/master/helper',
      keywords='amazon-textract-textractor amazon textract textractor helper',
      license="Apache License Version 2.0",
      classifiers=[
          "Development Status :: 4 - Beta",
          "Topic :: Utilities",
          'License :: OSI Approved :: Apache Software License',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3.8',
          'Programming Language :: Python :: 3.9',
      ],
      cmdclass={'install': FontInstaller},
      python_requires='>=3.6')
