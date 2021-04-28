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
print(get_string(textract_json=textract_json, table_format=Pretty_Print_Table_Format.csv))
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

