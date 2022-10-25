CLI
===

.. toctree::
   :maxdepth: 1

Textractor comes with its very own command line interface that aims to be easier to use than the default `boto3` interface by adding several quality of life improvements.

First install the package using :code:`pip install amazon-textract-textractor` make sure that you Python bin directory is added to PATH otherwise it will not find the executable. If you are not using a virtual environment this will probably be the case.

Available APIs
______________

:code:`Textractor` supports all Textract APIs and follow their official names as described here: https://docs.aws.amazon.com/textract/latest/dg/API_Operations.html. We use a single subcommand to fetch the results named :code:`GetResult`.

Synchronous APIs:

- DetectDocumentText/detect-document-text (Returns words and lines)
- AnalyzeDocument/analyze-document (Returns Forms, Tables and Query results)
- AnalyzeExpense/analyze-expense (Returns standardized fields for invoices)
- AnalyzeID/analyze-id (Returns standardized fields for driver's license and passports)

Asynchronous APIs: 

- StartDocumentTextDetection/start-document-text-detection
- StartDocumentAnalysis/start-document-analysis
- StartExpenseAnalysis/start-expense-analysis

Getting document text
_____________________

Now lets say you have a file and you wish to run OCR on it:

:code:`textractor detect-document-text your_file.png output.json`

This will call the Textract API and save the output to :code:`output.json`. You could use the Textractor python module to post-process those response afterwards.

Processing a directory of files
_______________________________

Now if instead of a file, you wished to process an entire directory of files. You could call the above on every file in the directory, but this would prove to be a very long process. Instead you can leverage Textract's ability to scale to your workload using the asynchronous API.

:code:`ls your_dir/ | xargs -I{} textractor start-document-text-detection {} --s3-upload-path s3://your-bucket/your-prefix/{}`

You can also parallelize it simply by adding -P8 (for 8 concurrent processes).

:code:`ls your_dir/ | xargs -P8 -I{} textractor start-document-text-detection {} --s3-upload-path s3://your-bucket/your-prefix/{} > output.txt`

You will notice that all you have in output.txt are UUID like this: :code:`628e39089ffa1b52d62d980ec1cf4f62cb7f785c83a708b2e17ebaaf21ad0d61`. Those are JobIDs and can be used to fetch the output of asynchronous operations.

Wait a few minutes (dependending on the number of files your processed) and then fetch the result  with :code:`GetResult`.

:code:`cat output.txt | xargs -I{} textractor get-result {} DETECT_TEXT {}.json`

Using :code:`-P8` would make the above faster, but be careful not to increase the concurrent process count too much as you might run into rate limiting issues (See https://docs.aws.amazon.com/textract/latest/dg/limits.html for more details).

Visualizing the output
______________________

The :code:`textractor` CLI allows you to overlay the output of Amazon Textract on top of an image for troubleshooting. It is only available for synchronous APIs (DetectDocumentText, AnalyzeDocument) and allows you to visualize words, lines, key and values, and tables.

In this example we will overlay words and tables on top of the :code:`tests/fixtures/amzn_q2.png` file. The image will be created in the same directory as the :code:`output.json` file under the name :code:`output.json.png`.

:code:`textractor analyze-document tests/fixtures/amzn_q2.png output.json --features TABLES --overlay WORDS TABLES` 

This will yield the following (click to enlarge):

.. image:: overlayer.png
  :width: 600
  :alt: Overlayer output

This document has a lot of small words, making it difficult to read. You can add :code:`--font-size-ratio` to the command to increase the font size.

:code:`textractor analyze-document tests/fixtures/amzn_q2.png output.json --features TABLES --overlay WORDS TABLES --font-size-ratio 1.0` (default it 0.75)

.. image:: overlayer_bigger.png
  :width: 600
  :alt: Overlayer output bigger

Reference
_________

.. argparse::
   :ref: textractor.cli.cli._build_parser
   :prog: textractor