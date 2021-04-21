# Textract-Overlayer

amazon-textract-overlayer provides functions to help overlay bounding boxes on documents.

# Install

```bash
> python -m pip install amazon-textract-overlayer
```

Make sure your environment is setup with AWS credentials through configuration files or environment variables or an attached role. (https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html)

# Samples

Primary method provided is get_bounding_boxes which returns bounding boxes based on the Textract_Type passed in.
Mostly taken from the ```amazon-textract``` command from the package ```amazon-textract-helper```.

This will return the bounding boxes for WORD and CELL data types.

```python
from textractoverlayer.t_overlay import DocumentDimensions, get_bounding_boxes
from textractcaller.t_call import Textract_Features, Textract_Types, call_textract

doc = call_textract(input_document=input_document, features=features)
# image is a PIL.Image.Image in this case
document_dimension:DocumentDimensions = DocumentDimensions(doc_width=image.size[0], doc_height=image.size[1])
overlay=[Textract_Types.WORD, Textract_Types.CELL]

bounding_box_list = get_bounding_boxes(textract_json=doc, document_dimensions=document_dimension, overlay_features=overlay)
```

The actual overlay drawing of bounding boxes for images is in the ```amazon-textract``` command from the package ```amazon-textract-helper```.
