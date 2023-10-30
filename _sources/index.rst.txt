Textractor Documentation
========================

.. image:: textractor_cropped.png
  :alt: Textractor

**Textractor** is a python package created to seamlessly work with 4 popular `Amazon Textract <https://docs.aws.amazon.com/textract/latest/dg/what-is.html>`_
APIs. These are the DocumentTextDetection, StartDocumentTextDetection, AnalyzeDocument and StartDocumentAnalysis endpoints. The package contains utilities to call Textract services, 
convert JSON responses from API calls to programmable objects, visualize entities on the document and export document data is compatible formats. 
It is intended to aid Textract customers in setting up their post-processing pipelines.

Previous work in this space has been made available in the following packages:

1. `amazon-textract-caller <https://pypi.org/project/amazon-textract-caller/>`_ (to call textract without the explicit use of boto3)

2. `amazon-textract-response-parser <https://pypi.org/project/amazon-textract-response-parser/>`_ (to parse the JSON response returned by Textract APIs)

3. `amazon-textract-overlayer <https://pypi.org/project/amazon-textract-overlayer/>`_ (to draw bounding boxes around the document entities on the document image)

4. `amazon-textract-prettyprinter <https://pypi.org/project/amazon-textract-prettyprinter/>`_ (to string represent document entities)

5. `amazon-textract-directional_finder <https://pypi.org/project/amazon-textract-directional_finder/>`_ (to perform geometric search on the document)


The `amazon-textract-caller <https://pypi.org/project/amazon-textract-caller/>`_ has been used as a dependency within this package 
with a wrapper around it to reduce the number of parameters the customer needs to pass. Additionally, newer input formats for the 
document have been provisioned with this package. 

The remaining packages have been refactored within this new package but the prominent functionalities are all made available to not disrupt
the requirements of the customer. 

This package also hosts newer features that haven't previously been implemented in existing packages. These include:

a. Semantic Document Search 

b. Query for key-values using keys

c. Table access with numpy indexing

d. New export formats with excel, csv and txt

e. Indication of duplicated document entities

f. Availability of all the above at :class:`Document` and :class:`Page` level.


.. toctree::
   :maxdepth: 4

Usage
=====
.. toctree::
   :maxdepth: 2

   installation
   using_in_lambda
   examples
   commandline

API Reference
=============

.. toctree::
   :maxdepth: 4

   textractor
   textractor.parsers
   textractor.entities
   textractor.visualizers
   textractor.data.constants
   textractor.data.text_linearization_config

