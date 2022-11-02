Using Textractor in AWS Lambda
============

.. toctree::
   :maxdepth: 3

Textractor uses Pillow for image manipulation which is a compiled dependency (i.e. not pure Python).
While we encourage you to build your own lambda layers, we received several requests mentioning that the process tedious,
which is why we also offer precompiled layers as zip files that you can directly upload to lambda.

The precompiled layers are rebuilt on release and can be downloaded here https://github.com/aws-samples/amazon-textract-textractor/actions/workflows/lambda_layers.yml.