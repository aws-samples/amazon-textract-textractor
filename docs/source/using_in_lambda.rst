Using Textractor in AWS Lambda
============

.. toctree::
   :maxdepth: 3

Textractor uses Pillow for image manipulation which is a compiled dependency (i.e. not pure Python).
While we encourage you to build your own lambda layers, we received several requests mentioning that the process tedious,
which is why we also offer precompiled layers as zip files that you can directly upload to lambda.

The precompiled layers are rebuilt on release and can be downloaded here https://github.com/aws-samples/amazon-textract-textractor/actions/workflows/lambda_layers.yml.

Step-by-step
------------

We provide a step by step through the AWS Console, but note that proceeding with the AWS CLI would also work. For brevity we assume that you already have an existing lambda.
You can find an excellent guide on how to create a lambda function here: 
https://docs.aws.amazon.com/lambda/latest/dg/getting-started.html. Note that your lambda function will need 
to have Textract access. Since we are targeting a wide range of use cases we will use the AmazonTextractFullAccess 
policy. We recommend that you review your lambda function and tailor the permission to your specific use case.

1. Download the precompiled layers from the GitHub Actions workflow. https://github.com/aws-samples/amazon-textract-textractor/actions/workflows/lambda_layers.yml

   a. Navigate to the page

   b. Click on "Lambda Layers"

   .. image:: images/lambda_tutorial/1b.png

   c. Scroll to the bottom of the page and download the package that matches your Python installation. Packages with the `-pdf` suffix contains `pdf2image` and allow you to process PDF documents. 

   .. image:: images/lambda_tutorial/1c.png

2. In your AWS Console, navigate to "Lambda" and click "Layers" in the sidebar to the left.

   .. image:: images/lambda_tutorial/2.png

   a. Click "Create layer"

   .. image:: images/lambda_tutorial/2a.png

   b. Fill-in the form and upload the .zip file you downloaded in step 1.

   .. image:: images/lambda_tutorial/2b.png

   c. Click "Create"

3. Navigate to your lambda

   a. Scroll down and click "Add a layer"

   .. image:: images/lambda_tutorial/3a.png

   b. Choose "Custom layers" and pick your amazon-textract-textractor layer

   c. Click "Add"

   .. image:: images/lambda_tutorial/3c.png

4. Update your code to use Textractor

   a. If using the PDF version you have to update the `PATH` and `LD_LIBRARY_PATH` environment variables through the lambda function configuration interface or directly in code with the `os` module: 

   .. code-block:: python

      os.environ["LD_LIBRARY_PATH"] = f"/opt/python/bin/:{os.environ['LD_LIBRARY_PATH']}"
      os.environ["PATH"] = f"/opt/python/bin/:{os.environ['PATH']}"