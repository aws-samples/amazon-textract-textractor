Installation
============

.. toctree::
   :maxdepth: 3

Official package
____________________________________

Textractor is available on PyPI and can be installed with :code:`pip install amazon-textract-textractor`. By default this will install the minimal version of textractor. The following extras can be used to add features:

- :code:`pdf` (:code:`pip install amazon-textract-textractor[pdf]`) includes :code:`pdf2image` and enables PDF rasterization in Textractor. Note that this is **not** necessary to call Textract with a PDF file.
- :code:`torch` (:code:`pip install amazon-textract-textractor[torch]`) includes :code:`sentence_transformers` for better word search and matching. This will work on CPU but be noticeably slower than non-machine learning based approaches.
- :code:`dev` (:code:`pip install amazon-textract-textractor[dev]`) includes all the dependencies above and everything else needed to test the code.

You can pick several extras by separating the labels with commas like this :code:`pip install amazon-textract-textractor[pdf,torch]`.

From Source
___________

To install the package, clone the repository with the following command -

:code:`git clone git@github.com:aws-samples/amazon-textract-textractor.git`

Navigate into the amazon-textract-textractor directory on the terminal and run these commands.

To install requirements :code:`pip install -r requirements.txt`

Then install the package with :code:`pip install -e .`

Try it out
___________

The :file:`Demo.ipynb` can be used as a reference to understand some functionalities hosted by the package.
Additionally, `docs/tests/notebooks/` have some tutorials you can try out.