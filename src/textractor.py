from tdp import DocumentProcessor
import os
from og import OutputGenerator
from helper import FileHelper, S3Helper
import argparse
from textract_features import TEXTRACT_FEATURES, TEXTRACT_SUFFIXES
from typing import Optional


class Textractor:
    def __init__(self,
                 s3_bucket: Optional[str],
                 documents: "list[str]",
                 region: str,
                 textract_features: "list[TEXTRACT_FEATURES]",
                 insights: bool,
                 medical_insights=bool,
                 translate=bool):
        self.s3_bucket = s3_bucket
        self.documents = documents
        self.region = region
        self.textract_features = textract_features
        self.insights = insights
        self.medical_insights = medical_insights
        self.translate = translate

    @staticmethod
    def get_document_list(document_path: str) -> "list[str]":
        try:
            file_list = S3Helper.get_s3_object_keys(
                s3_object=document_path, allowedFileTypes=TEXTRACT_SUFFIXES)
        except ValueError:
            if os.path.isfile(document_path):
                file_list = [document_path]
            else:
                file_list = FileHelper.getFileNames(
                    document_path, allowedLocalFileTypes=TEXTRACT_SUFFIXES)
        return file_list

    def processDocument(self, bucket_name, document, s3_region,
                        textract_features: "list[TEXTRACT_FEATURES]"):
        print('=' * (len(document) + 30))

        # Get document textracted
        dp = DocumentProcessor(bucket_name,
                               document,
                               s3_region,
                               textract_features=textract_features)
        response = dp.run()

        if (response):
            print("Recieved Textract response...")
            #FileHelper.writeToFile("temp-response.json", json.dumps(response))

            #Generate output files
            print("Generating output...")
            name, ext = FileHelper.getFileNameAndExtension(document)
            opg = OutputGenerator(response, "{}-{}".format(name, ext),
                                  self.textract_features)
            opg.run()

            if (self.insights or self.medical_insights or self.translate):
                opg.generateInsights(self.insights, self.medical_insights,
                                     self.translate, self.region)

            print("{} textracted successfully.".format(document))
        else:
            print(f"Could not generate output for {document}.")

    @staticmethod
    def get_textract_features(text: str, forms: str,
                              tables: str) -> "list[TEXTRACT_FEATURES]":
        textract_features: "list[TEXTRACT_FEATURES]" = list()
        if text:
            textract_features.append(TEXTRACT_FEATURES.TEXT)
        if forms:
            textract_features.append(TEXTRACT_FEATURES.FORMS)
        if tables:
            textract_features.append(TEXTRACT_FEATURES.TABLES)
        return textract_features

    def run(self):
        print("\n")
        print('*' * 60)
        print("Total input documents: {}".format(len(self.documents)))
        print('*' * 60)
        for idx, document in enumerate(self.documents):
            print("\nTextracting Document # {}: {}".format(idx + 1, document))
            self.processDocument(bucket_name=s3_bucket,
                                 document=document,
                                 s3_region=args.region,
                                 textract_features=self.textract_features)

            remaining = len(document_list) - (idx + 1)

            if (remaining > 0):
                print("\nRemaining documents: {}".format(remaining))

        print("\n")
        print('*' * 60)
        print("Successfully textracted documents: {}".format(
            len(self.documents)))
        print('*' * 60)
        print("\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--documents",
        required=True,
        metavar="LOCATION_OF_DOCUMENT(S)",
        help=
        "either location of one document or path to a documents. Documents can be on s3:// or local filepath"
    )
    textract_features_group = parser.add_argument_group("textract_features")
    textract_features_group.add_argument("--text", action='store_true')
    textract_features_group.add_argument("--forms", action='store_true')
    textract_features_group.add_argument("--tables", action='store_true')
    parser.add_argument("--region",
                        metavar="AWS_REGION",
                        help="AWS Region code (e. g. us-east-1)")
    parser.add_argument(
        "--insights",
        action='store_true',
        help=
        "Calls Amazon Comprehend, a natural language processing (NLP) service that uses machine learning to find insights and relationships in text. No machine learning experience required."
    )
    parser.add_argument(
        "--medical-insights",
        action='store_true',
        help=
        "Calls Amazon Comprehend Medical, a HIPAA-eligible natural language processing (NLP) service that uses machine learning to extract health data from medical text–no machine learning experience is required"
    )
    parser.add_argument(
        "--translate",
        metavar='LANGUAGE_CODE',
        help=
        "Target Language Code for Amazon Translate (https://docs.aws.amazon.com/translate/latest/dg/what-is.html)"
    )
    args = parser.parse_args()
    if not args.text and not args.forms and not args.tables:
        parser.error("at least one of --text, --forms or --tables is required")

    path_is_s3 = S3Helper.path_is_s3(args.documents)
    s3_bucket = None
    if path_is_s3:
        s3_bucket, _ = S3Helper.split_bucket_and_key(args.documents)

    document_list = Textractor.get_document_list(args.documents)
    textract_features = Textractor.get_textract_features(
        args.text, args.forms, args.tables)
    textractor = Textractor(s3_bucket=s3_bucket,
                            documents=document_list,
                            region=args.region,
                            textract_features=textract_features,
                            insights=args.insights,
                            medical_insights=args.medical_insights,
                            translate=args.translate)
    textractor.run()
