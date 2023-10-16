# Textract-Caller

amazon-textract-caller provides a collection of ready to use functions and sample implementations to speed up the evaluation and development for any project using Amazon Textract.

Making it easy to call Amazon Textract regardless of file type and location.

## Install

```bash
> python -m pip install amazon-textract-caller
```

## Functions

```python
from textractcaller import call_textract
def call_textract(input_document: Union[str, bytes],
                  features: Optional[List[Textract_Features]] = None,
                  queries_config: Optional[QueriesConfig] = None,
                  output_config: Optional[OutputConfig] = None,
                  adapters_config: Optional[AdaptersConfig] = None,
                  kms_key_id: str = "",
                  job_tag: str = "",
                  notification_channel: Optional[NotificationChannel] = None,
                  client_request_token: str = "",
                  return_job_id: bool = False,
                  force_async_api: bool = False,
                  call_mode: Textract_Call_Mode = Textract_Call_Mode.DEFAULT,
                  boto3_textract_client=None,
                  job_done_polling_interval=1) -> dict:
```

Also useful when receiving the JSON response from an asynchronous job (start_document_text_detection or start_document_analysis)

```python
from textractcaller import get_full_json
def get_full_json(job_id: str = None,
                  textract_api: Textract_API = Textract_API.DETECT,
                  boto3_textract_client=None)->dict:
```

And when receiving the JSON from the OutputConfig location, this method is useful as well.

```python
from textractcaller import get_full_json_from_output_config
def get_full_json_from_output_config(output_config: OutputConfig = None,
                                     job_id: str = None,
                                     s3_client = None)->dict:
```

## Samples

### Calling with file from local filesystem only with detect_text

```python
textract_json = call_textract(input_document="/folder/local-filesystem-file.png")
```

### Calling with file from local filesystem only detect_text and using in Textract Response Parser

(needs trp dependency through ```python -m pip install amazon-textract-response-parser```)

```python
import json
from trp import Document
from textractcaller import call_textract

textract_json = call_textract(input_document="/folder/local-filesystem-file.png")
d = Document(textract_json)
```

### Calling with Queries for a multi-page document and extract the Answers

sample also uses the amazon-textract-response-parser

```
python -m pip install amazon-textract-caller amazon-textract-response-parser
```

```python
import textractcaller as tc
import trp.trp2 as t2
import boto3

textract = boto3.client('textract', region_name="us-east-2")
q1 = tc.Query(text="What is the employee SSN?", alias="SSN", pages=["1"])
q2 = tc.Query(text="What is YTD gross pay?", alias="GROSS_PAY", pages=["2"])
textract_json = tc.call_textract(
    input_document="s3://amazon-textract-public-content/blogs/2-pager.pdf",
    queries_config=tc.QueriesConfig(queries=[q1, q2]),
    features=[tc.Textract_Features.QUERIES],
    force_async_api=True,
    boto3_textract_client=textract)
t_doc: t2.TDocument = t2.TDocumentSchema().load(textract_json)  # type: ignore
for page in t_doc.pages:
    query_answers = t_doc.get_query_answers(page=page)
    for x in query_answers:
        print(f"{x[1]},{x[2]}")
```

### Calling with Custom Queries for a multi-page document using an adapter

sample also uses the amazon-textract-response-parser

```
python -m pip install amazon-textract-caller amazon-textract-response-parser
```

```python
import textractcaller as tc
import trp.trp2 as t2
import boto3

textract = boto3.client('textract', region_name="us-east-2")
q1 = tc.Query(text="What is the employee SSN?", alias="SSN", pages=["1"])
q2 = tc.Query(text="What is YTD gross pay?", alias="GROSS_PAY", pages=["2"])
adapter1 = tc.Adapter(adapter_id="2e9bf1c4aa31", version="1", pages=["1"])
textract_json = tc.call_textract(
    input_document="s3://amazon-textract-public-content/blogs/2-pager.pdf",
    queries_config=tc.QueriesConfig(queries=[q1, q2]),
    adapters_config=tc.AdaptersConfig(adapters=[adapter1])
    features=[tc.Textract_Features.QUERIES],
    force_async_api=True,
    boto3_textract_client=textract)
t_doc: t2.TDocument = t2.TDocumentSchema().load(textract_json)  # type: ignore
for page in t_doc.pages:
    query_answers = t_doc.get_query_answers(page=page)
    for x in query_answers:
        print(f"{x[1]},{x[2]}")
```


### Calling with file from local filesystem with TABLES features

```python
from textractcaller import call_textract, Textract_Features
features = [Textract_Features.TABLES]
response = call_textract(
    input_document="/folder/local-filesystem-file.png", features=features)
```

### Call with images located on S3 but force asynchronous API

```python
from textractcaller import call_textract
response = call_textract(input_document="s3://some-bucket/w2-example.png", force_async_api=True)
```

### Call with OutputConfig, Customer-Managed-Key

```python
from textractcaller import call_textract
from textractcaller import OutputConfig, Textract_Features
output_config = OutputConfig(s3_bucket="somebucket-encrypted", s3_prefix="output/")
response = call_textract(input_document="s3://someprefix/somefile.png",
                          force_async_api=True,
                          output_config=output_config,
                          kms_key_id="arn:aws:kms:us-east-1:12345678901:key/some-key-id-ref-erence",
                          return_job_id=False,
                          job_tag="sometag",
                          client_request_token="sometoken")

```

### Call with PDF located on S3 and force return of JobId instead of JSON response

```python
from textractcaller import call_textract
response = call_textract(input_document="s3://some-bucket/some-document.pdf", return_job_id=True)
job_id = response['JobId']
```
