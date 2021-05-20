# Textract-Pipeline-PageDimensions

Provides functions to add page dimensions with doc_width and doc_height to the Textract JSON schema for the PAGE blocks under the custom attribute in the form of:

e. g.

```
{'PageDimension': {'doc_width': 1549.0, 'doc_height': 370.0} }
```

# Install

```bash
> python -m pip install amazon-textract-pipeline-pagedimensions
```

Make sure your environment is setup with AWS credentials through configuration files or environment variables or an attached role. (https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html)

# Samples

## Add Page dimensions for a local file

sample uses amazon-textract-caller amazon-textract-pipeline-pagedimensions

```bash
python -m pip install amazon-textract-caller
```

```python
from textractpagedimensions.t_pagedimensions import add_page_dimensions
from textractcaller.t_call import call_textract
from trp.trp2 import TDocument, TDocumentSchema

j = call_textract(input_document='<path to some image file>')
t_document: TDocument = TDocumentSchema().load(j)
add_page_dimensions(t_document=t_document, input_document=input_file)
print(t_document.pages[0].custom['PageDimension']) 
# output will be something like this:
# {
#     'doc_width': 1544,
#     'doc_height': 1065
# }
```

## Using the Amazon Textact Helper command line tool with PageDimensions

Together with the Amazon Textract Helper and Amazon Textract Response Parser, we can build a pipeline that includes information about PageDimension and Orientation of pages
as a short demonstration on the information that is added to the Textract JSON.

```bash
> python -m pip install amazon-textract-helper amazon-textract-response-parser amazon-textract-pipeline-pagedimensions
> amazon-textract --input-document "s3://amazon-textract-public-content/blogs/2-pager-different-dimensions.pdf" | amazon-textract-pipeline-pagedimensions --input-document "s3://amazon-textract-public-content/blogs/2-pager-different-dimensions.pdf"  | amazon-textract-pipeline --components add_page_orientation | jq '.Blocks[] | select(.BlockType=="PAGE") | .Custom'

{
  "PageDimension": {
    "doc_width": 1549,
    "doc_height": 370
  },
  "Orientation": 0
}
{
  "PageDimension": {
    "doc_width": 1079,
    "doc_height": 505
  },
  "Orientation": 0
}
```
