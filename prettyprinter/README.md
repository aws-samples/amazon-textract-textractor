# Textract-PrettyPrinter

amazon-textract-prettyprinter

# Install

```bash
> python -m pip install amazon-textract-prettyprinter
```

Make sure your environment is setup with AWS credentials through configuration files or environment variables or an attached role. (https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html)

# Samples

## Get string for TABLES using the default method

```
from textractcaller.t_call import call_textract
from textractprettyprinter.t_pretty_print import Textract_Pretty_Print, get_string

doc = call_textract(input_document=input_document, features=features)
get_string(textract_json_string=doc, output_type=Textract_Pretty_Print.TABLES)
```
## Get table with custom format

```
from textractcaller.t_call import call_textract
from textractprettyprinter.t_pretty_print import Textract_Pretty_Print, get_string

doc = call_textract(input_document=input_document, features=features)
get_tables_string(textract_json_string=doc)
```

