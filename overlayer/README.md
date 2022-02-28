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

The actual overlay drawing of bounding boxes for images is in the ```amazon-textract``` command from the package ```amazon-textract-helper``` and looks like this:

```python
from PIL import Image, ImageDraw

image = Image.open(input_document)
rgb_im = image.convert('RGB')
draw = ImageDraw.Draw(rgb_im)

# check the impl in amazon-textract-helper for ways to associate different colors to types
for bbox in bounding_box_list:
    draw.rectangle(xy=[bbox.xmin, bbox.ymin, bbox.xmax, bbox.ymax], outline=(128, 128, 0), width=2)

rgb_im.show()
```

The draw bounding boxes within PDF documents the following code can be used:

```python
import fitz

# for local stored files
file_path = "<<replace with the local path to your pdf file>>"
doc = fitz.open(file_path)
# for files stored in S3 the streaming object can be used
# doc = fitz.open(stream="<<replace with stream_object_variable>>", filetype="pdf")

# draw boxes
for p, page in enumerate(doc):
    p += 1
    for bbox in bounding_box_list:
        if bbox.page_number == p:
            page.draw_rect(
                [bbox.xmin, bbox.ymin, bbox.xmax, bbox.ymax], color=(0, 1, 0), width=2
            )

# save file locally 
doc.save("<<local path for output file>>")

```