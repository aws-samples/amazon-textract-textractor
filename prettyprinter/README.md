# Textract-PrettyPrinter

Provides functions to format the output received from Textract in more easily consumable formats incl. CSV or Markdown.
amazon-textract-prettyprinter

# Install

```bash
> python -m pip install amazon-textract-prettyprinter
```

Make sure your environment is setup with AWS credentials through configuration files or environment variables or an attached role. (https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html)


# Samples

## Get FORMS and TABLES as CSV

```python
from textractcaller.t_call import call_textract, Textract_Features
from textractprettyprinter.t_pretty_print import Pretty_Print_Table_Format, Textract_Pretty_Print, get_string

textract_json = call_textract(input_document=input_document, features=[Textract_Features.FORMS, Textract_Features.TABLES])
print(get_string(textract_json=textract_json,
               table_format=Pretty_Print_Table_Format.csv,
               output_type=[Textract_Pretty_Print.TABLES, Textract_Pretty_Print.FORMS]))
```

## Get string for TABLES using the get_string method

```python
from textractcaller.t_call import call_textract, Textract_Features
from textractprettyprinter.t_pretty_print import Textract_Pretty_Print, get_string

textract_json = call_textract(input_document=input_document, features=[Textract_Features.TABLES])
get_string(textract_json=textract_json, output_type=Textract_Pretty_Print.TABLES)
```

## Print out tables in LaTeX format

```python
from textractcaller.t_call import call_textract, Textract_Features
from textractprettyprinter.t_pretty_print import Textract_Pretty_Print, get_string

textract_json = call_textract(input_document=input_document, features=[Textract_Features.FORMS, Textract_Features.TABLES])
get_tables_string(textract_json=textract_json, table_format=Pretty_Print_Table_Format.latex)
```

## Get linearized text from LAYOUT using get_text_from_layout_json method

Generates a dictionary of linearized text from the Textract JSON response with LAYOUT, and optionally writes linearized plain text files to local file system or Amazon S3. It can take either per page JSON from AnalyzeDocument API, or a single combined JSON with all the pages created from StartDocumentAnalysis output JSONs.
    
```python
from textractcaller.t_call import call_textract, Textract_Features
from textractprettyprinter.t_pretty_print import get_text_from_layout_json

textract_json = call_textract(input_document=input_document, features=[Textract_Features.LAYOUT, Textract_Features.TABLES])
layout = get_text_from_layout_json(textract_json=textract_json)

full_text = layout[1]
print(full_text)
```

In addition to `textract_json`, the `get_text_from_layout_json` function can take the following additional parameters

- `table_format` (str, optional): Format of tables within the document. Supports all python-tabulate table formats. See [tabulate](https://github.com/gregbanks/python-tabulate) for supported table formats. Defaults to `grid`.
- `exclude_figure_text` (bool, optional): If set to True, excludes text extracted from figures in the document. Defaults to `False`.
- `exclude_page_header` (bool, optional): If set to True, excludes the page header from the linearized text. Defaults to `False`.
- `exclude_page_footer` (bool, optional): If set to True, excludes the page footer from the linearized text. Defaults to `False`.
- `exclude_page_number` (bool, optional): If set to True, excludes the page number from the linearized text. Defaults to `False`.
- `skip_table` (bool, optional): If set to True, skips including the table in the linearized text. Defaults to `False`.
- `save_txt_path` (str, optional): Path to save the output linearized text to files. Either a local file system path or Amazon S3 path can be specified in `s3://bucket_name/prefix/` format. Files will be saved with `<page_number>.txt` naming convention.
- `generate_markdown` (bool, optional): If set to `True`, generates markdown formatted linearized text. Defaults to `False`.
