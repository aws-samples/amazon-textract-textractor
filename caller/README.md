# Textract-Caller

amazon-textract-caller provides a collection of ready to use functions and sample implementations to speed up the evaluation and development for any project using Amazon Textract.

Making it easy to call Amazon Textract regardless of file type and location.

```
def call_textract(input_document: Union[str, bytearray],
                  features: List[Textract_Features] = None,
                  output_config: OutputConfig = None,
                  kms_key_id: str = None,
                  job_tag: str = None,
                  notification_channel: NotificationChannel = None,
                  client_request_token: str = None,
                  return_job_id: bool = False,
                  force_async_api: bool = False) -> str:
```

## Samples

### Calling with file from local filesystem only OCR
```
textract_json = call_textract(input_document="/folder/local-filesystem-file.png")
```

### Calling with file from local filesystem only OCR and using in Textract Response Parser

(needs trp dependency through```python -m pip install amazon-textract-response-parser```)
```
import json
from trp import Document
from textracthelper.t_call call_textract

textract_json = call_textract(input_document="/folder/local-filesystem-file.png")
d = Document(json.loads(response))
```


### Calling with file from local filesystem with TABLES features

```
from textracthelper.t_call call_textract, Textract_Features
features = [Textract_Features.TABLES]
response = call_textract(
    input_document="/folder/local-filesystem-file.png", features=features)
```

### Call with images located on S3 but force asynchronous API

```
from textracthelper.t_call call_textract
response = call_textract(input_document="s3://some-bucket/w2-example.png", force_async_api=True)
```

### Call with OutputConfig, Customer-Managed-Key

```
from textracthelper.t_call call_textract
from textractcaller.t_call import OutputConfig, Textract_Features
output_config = OutputConfig(s3_bucket="somebucket-encrypted", s3_prefix="output/")
response = call_textract(input_document="s3://someprefix/somefile.png",
                          force_async_api=True,
                          output_config=output_config,
                          kms_key_id="arn:aws:kms:us-east-1:12345678901:key/some-key-id-ref-erence",
                          return_job_id=False,
                          job_tag="sometag",
                          client_request_token="sometoken")

```
