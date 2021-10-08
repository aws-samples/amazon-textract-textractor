# Textract-Pipeline-GeoFinder

Provides functions to use geometric information to extract information.

Use cases include:
* Give context to key/value pairs from the Amazon Textract AnalyzeDocument API for FORMS
* Find values in specific areas

# Install

```bash
> python -m pip install amazon-textract-geofinder
```

Make sure your environment is setup with AWS credentials through configuration files or environment variables or an attached role. (https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html)

# Concept

To find information in a document based on geometry with this library the main advantage over defining x,y coordinates where the expected value should be is the concept of an area.

An area is ultimately defined by a box with x_min, y_min, x_max, y_max coordinates but can be defined by finding words/phrases in the document and then use to create the area.

From there functions to parse the information in the area help to extract the information. E. g. by defining the area based on the question like 'Did you feel fever or feverish lately?' we can associate the answers to it and create a new key/value pair specific to this question.


# Samples

## Get context for key value pairs

Sample image:

<img src="./tests/data/patient_intake_form_sample.jpg" width=300> 

The Amazon Textract AnalyzeDocument API with the FORMS feature returns the following keys:

| Key                                          | Value          |
|----------------------------------------------|----------------|
| First Name:                                  | ALEJANDRO      |
| First Name:                                  | CARLOS         |
| Relationship to Patient:                     | BROTHER        |
| First Name:                                  | JANE           |
| Marital Status:                              | MARRIED        |
| Phone:                                       | 646-555-0111   |
| Last Name:                                   | SALAZAR        |
| Phone:                                       | 212-555-0150   |
| Relationship to Patient:                     | FRIEND         |
| Last Name:                                   | ROSALEZ        |
| City:                                        | ANYTOWN        |
| Phone:                                       | 650-555-0123   |
| Address:                                     | 123 ANY STREET |
| Yes                                          | SELECTED       |
| Yes                                          | NOT_SELECTED   |
| Date of Birth:                               | 10/10/1982     |
| Last Name:                                   | DOE            |
| Sex:                                         | M              |
| Yes                                          | NOT_SELECTED   |
| Yes                                          | NOT_SELECTED   |
| Yes                                          | NOT_SELECTED   |
| State:                                       | CA             |
| Zip Code:                                    | 12345          |
| Email Address:                               |                |
| No                                           | NOT_SELECTED   |
| No                                           | SELECTED       |
| No                                           | NOT_SELECTED   |
| Yes                                          | SELECTED       |
| No                                           | SELECTED       |
| No                                           | SELECTED       |
| No                                           | SELECTED       |


But the information to which section of the document the individual keys belong is not obvious. Most keys appear multiple times and we want to give them context to associate them with the 'Patient', 'Emergency Contact 1', 'Emergency Contact 2' or specific questions.


This Jupyter notebook that walks through the sample: [sample notebook](./geofinder-sample-notebook.ipynb)
Make sure to have AWS credentials setup when starting the notebook locally or use a SageMaker notebook with a role including permissions for Amazon Textract. 

This code snippet is take from the notebook.

```bash
python -m pip install amazon-textract-helper amazon-textract-geofinder
```

```python
from textractgeofinder.ocrdb import AreaSelection
from textractgeofinder.tgeofinder import KeyValue, TGeoFinder, AreaSelection, SelectionElement
from textractprettyprinter.t_pretty_print import get_forms_string
from textractcaller import call_textract
from textractcaller.t_call import Textract_Features

import trp.trp2 as t2

image_filename='./tests/data/patient_intake_form_sample.jpg'

j = call_textract(input_document=image_filename, features=[Textract_Features.FORMS])


t_document = t2.TDocumentSchema().load(j)
doc_height = 1000
doc_width = 1000
geofinder_doc = TGeoFinder(j, doc_height=doc_height, doc_width=doc_width)

def set_hierarchy_kv(list_kv: list[KeyValue], t_document: t2.TDocument, page_block: t2.TBlock, prefix="BORROWER"):
    for x in list_kv:
        t_document.add_virtual_key_for_existing_key(key_name=f"{prefix}_{x.key.text}",
                                                    existing_key=t_document.get_block_by_id(x.key.id),
                                                    page_block=page_block)
# patient information
patient_information = geofinder_doc.find_phrase_on_page("patient information")[0]
emergency_contact_1 = geofinder_doc.find_phrase_on_page("emergency contact 1:", min_textdistance=0.99)[0]
top_left = t2.TPoint(y=patient_information.ymax, x=0)
lower_right = t2.TPoint(y=emergency_contact_1.ymin, x=doc_width)
form_fields = geofinder_doc.get_form_fields_in_area(
    area_selection=AreaSelection(top_left=top_left, lower_right=lower_right))
set_hierarchy_kv(list_kv=form_fields, t_document=t_document, prefix='PATIENT', page_block=t_document.pages[0])

set_hierarchy_kv(list_kv=form_fields, t_document=t_document, prefix='PATIENT', page_block=t_document.pages[0])

print(get_forms_string(t2.TDocumentSchema().dump(t_document)))
```

| Key                     | Value          |
|-------------------------|----------------|
| ...                     | ...            |
| PATIENT_first name:     | ALEJANDRO      |
| PATIENT_address:        | 123 ANY STREET |
| PATIENT_sex:            | M              |
| PATIENT_state:          | CA             |
| PATIENT_zip code:       | 12345          |
| PATIENT_marital status: | MARRIED        |
| PATIENT_last name:      | ROSALEZ        |
| PATIENT_phone:          | 646-555-0111   |
| PATIENT_email address:  |                |
| PATIENT_city:           | ANYTOWN        |
| PATIENT_date of birth:  | 10/10/1982     |

## Using the Amazon Textact Helper command line tool with the sample

This will show the full result, like the notebook.

```bash
> python -m pip install amazon-textract-helper amazon-textract-geofinder
> cat tests/data/patient_intake_form_sample.json| bin/amazon-textract-geofinder | amazon-textract --stdin --pretty-print FORMS
```

| Key                     | Value          |
|-------------------------|----------------|
| First Name:                                  | ALEJANDRO      |
| First Name:                                  | CARLOS         |
| Relationship to Patient:                     | BROTHER        |
| First Name:                                  | JANE           |
| Marital Status:                              | MARRIED        |
| Phone:                                       | 646-555-0111   |
| Last Name:                                   | SALAZAR        |
| Phone:                                       | 212-555-0150   |
| Relationship to Patient:                     | FRIEND         |
| Last Name:                                   | ROSALEZ        |
| City:                                        | ANYTOWN        |
| Phone:                                       | 650-555-0123   |
| Address:                                     | 123 ANY STREET |
| Yes                                          | SELECTED       |
| Yes                                          | NOT_SELECTED   |
| Date of Birth:                               | 10/10/1982     |
| Last Name:                                   | DOE            |
| Sex:                                         | M              |
| Yes                                          | NOT_SELECTED   |
| Yes                                          | NOT_SELECTED   |
| Yes                                          | NOT_SELECTED   |
| State:                                       | CA             |
| Zip Code:                                    | 12345          |
| Email Address:                               |                |
| No                                           | NOT_SELECTED   |
| No                                           | SELECTED       |
| No                                           | NOT_SELECTED   |
| Yes                                          | SELECTED       |
| No                                           | SELECTED       |
| No                                           | SELECTED       |
| No                                           | SELECTED       |
| PATIENT_first name:                          | ALEJANDRO      |
| PATIENT_address:                             | 123 ANY STREET |
| PATIENT_sex:                                 | M              |
| PATIENT_state:                               | CA             |
| PATIENT_zip code:                            | 12345          |
| PATIENT_marital status:                      | MARRIED        |
| PATIENT_last name:                           | ROSALEZ        |
| PATIENT_phone:                               | 646-555-0111   |
| PATIENT_email address:                       |                |
| PATIENT_city:                                | ANYTOWN        |
| PATIENT_date of birth:                       | 10/10/1982     |
| EMERGENCY_CONTACT_1_first name:              | CARLOS         |
| EMERGENCY_CONTACT_1_phone:                   | 212-555-0150   |
| EMERGENCY_CONTACT_1_relationship to patient: | BROTHER        |
| EMERGENCY_CONTACT_1_last name:               | SALAZAR        |
| EMERGENCY_CONTACT_2_first name:              | JANE           |
| EMERGENCY_CONTACT_2_phone:                   | 650-555-0123   |
| EMERGENCY_CONTACT_2_last name:               | DOE            |
| EMERGENCY_CONTACT_2_relationship to patient: | FRIEND         |
| FEVER->YES                                   | SELECTED       |
| FEVER->NO                                    | NOT_SELECTED   |
| SHORTNESS->YES                               | NOT_SELECTED   |
| SHORTNESS->NO                                | SELECTED       |
| COUGH->YES                                   | NOT_SELECTED   |
| COUGH->NO                                    | SELECTED       |
| LOSS_OF_TASTE->YES                           | NOT_SELECTED   |
| LOSS_OF_TASTE->NO                            | SELECTED       |
| COVID_CONTACT->YES                           | SELECTED       |
| COVID_CONTACT->NO                            | NOT_SELECTED   |
| TRAVEL->YES                                  | NOT_SELECTED   |
| TRAVEL->NO                                   | SELECTED       |
