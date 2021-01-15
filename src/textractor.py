import argparse
import os
import sys
import time
import traceback
from types import SimpleNamespace
from urllib.parse import urlparse

import boto3

from tdp import DocumentProcessor
from og import OutputGenerator
from helper import FileHelper, S3Helper

class Textractor:
    def parseInput(self, args):
        parser = argparse.ArgumentParser(
            description="Textractor: Easily process documents with Amazon Textract",
        )
        parser.add_argument(
            "--documents", type=str, required=True,
            help="Document(s) to process: path to a local file or folder, or an s3://... URI",
        )
        parser.add_argument(
            "--output", type=str, default=".",
            help="Local folder to save outputs to: Defaults to current working directory",
        )
        parser.add_argument(
            "--region", type=str, default=None,
            help="AWS Region to use for API calls, e.g. us-east-1 (Ignored if processing S3 input)",
        )
        parser.add_argument(
            "--text", action="store_true",
            help="Set this flag to extract the plain text from the document",
        )
        parser.add_argument(
            "--forms", action="store_true",
            help="Set this flag to extract form field key-value pairs from the document",
        )
        parser.add_argument(
            "--tables", action="store_true",
            help="Set this flag to extract structured table data from the document",
        )
        parser.add_argument(
            "--insights", action="store_true",
            help="Set this flag to extract structured table data from the document",
        )
        parser.add_argument(
            "--medical-insights", action="store_true",
            help="Set this flag to extract structured table data from the document",
        )
        parser.add_argument(
            "--translate", type=str, default=None,
            help="Optional language code to translate extracted text into with Amazon Translate, e.g. es",
        )
        parser.add_argument(
            "--fail-on-error", action="store_true",
            help="Set this flag to fail the job if any document fails to process",
        )
        parser.add_argument(
            "--flatten-folders", action="store_true",
            help="Set this flag to output a flat set of files only, instead of preserving input subfolders",
        )

        # Parse the raw args first:
        config = parser.parse_args(args)

        # Create the output folder if it doesn't exist already:
        FileHelper.ensureFolder(config.output)

        # Post-validations and transformations:
        # - Expand ips.documents to a list of individual files
        # - Set default 'us-east-1' or override region if S3 input specified
        inputs = SimpleNamespace(bucket=None, paths=[], basePath=None)
        if(config.documents.lower().startswith("s3://")):
            o = urlparse(config.documents)
            bucketName = o.netloc
            s3Path = o.path[1:]
            inputs.bucket = bucketName

            bucketRegion = S3Helper.getS3BucketRegion(bucketName)
            if(bucketRegion):
                config.region = bucketRegion  # Explicitly override
            else:
                config.region = "us-east-1"

            if(s3Path.endswith("/")):
                allowedFileTypes = ["jpg", "jpeg", "png", "pdf"]
                # TODO: Parameterize or remove max_pages=1
                # Keeping this for now to preserve previous behaviour but I'd argue this non-configurable
                # limit is a bug or at least a significant flaw.
                inputs.paths = S3Helper.getFileNames(
                    bucketRegion,
                    bucketName,
                    s3Path,
                    1,
                    allowedFileTypes,
                )
                inputs.basePath = s3Path
            else:
                inputs.basePath = s3Path.rpartition("/")[0] or "."
                if(S3Helper.checkObjectExists(bucketRegion, bucketName, s3Path)):
                    inputs.paths = [s3Path]
                else:
                    raise ValueError(
                        (
                            "S3 Object not found (Please use a trailing '/' to specify a folder, or '*' to"
                            "specify a prefix). Got: {}"
                        ).format(config.documents)
                    )
        else:
            if(config.documents.endswith(os.path.sep)):
                allowedFileTypes = ["jpg", "jpeg", "png"]
                inputs.paths = FileHelper.getFileNames(config.documents, allowedFileTypes)
                inputs.basePath = config.documents
            else:
                if(FileHelper.checkFileExists(config.documents)):
                    inputs.paths = [config.documents]
                    inputs.basePath = os.path.dirname(config.documents) or "."
                else:
                    raise ValueError(
                        "File not found (Please include a trailing slash to specify a folder): {}".format(
                            config.documents,
                        )
                    )
        if(len(inputs.paths) == 0):
            raise ValueError("No documents found under folder/prefix {} matching allowed types {}".format(
                config.documents,
                allowedFileTypes,
            ))

        return config, inputs

    def processDocument(self, config, path, pathBase=None, bucket=None, i=None):
        print("\nTextracting Document # {}: {}".format(i, path))
        print("=" * (len(path) + 30))

        # Get document textracted
        dp = DocumentProcessor(bucket, path, config.region, config.text, config.forms, config.tables)
        response = dp.run()

        if(not response):
            raise ValueError("Empty response from DocumentProcessor")

        print("Recieved Textract response...")
        #FileHelper.writeToFile("temp-response.json", json.dumps(response))

        #Generate output files
        print("Generating output...")
        name, ext = FileHelper.getFileNameAndExtension(path)
        if(config.flatten_folders):
            outFolder = config.output
        else:
            outFolder = FileHelper.mapSubFolder(pathBase, path, config.output)
            FileHelper.ensureFolder(outFolder)
        opg = OutputGenerator(
            response,
            "{}-{}".format(name, ext),
            config.forms,
            config.tables,
            basePath=outFolder,
        )
        opg.run()

        if(config.insights or config.medical_insights or config.translate):
            opg.generateInsights(
                config.insights,
                config.medical_insights,
                config.translate,
                config.region,
            )

    def run(self, args=None):
        """Run the Textractor utility

        Parameters
        ----------
        args : List[str] (Optional)
            By default, the current process' command line arguments will be used. Use this parameter to
            override instead, if you need. E.g. ["--documents", "./myfolder/", "--forms"]
        """

        config, inputs = self.parseInput(args)

        totalDocuments = len(inputs.paths)
        successes = 0

        print("\n")
        print("*" * 60)
        print("Total input documents: {}".format(totalDocuments))
        print("*" * 60)

        for i, docPath in enumerate(inputs.paths, start=1):
            try:
                self.processDocument(config, docPath, inputs.basePath, bucket=inputs.bucket, i=i)
                successes += 1
                print("{} textracted successfully.".format(docPath))
            except Exception as e:
                if(config.fail_on_error):
                    raise e
                else:
                    print("{} failed to process.".format(docPath))
                    traceback.print_exc()

            if(i < totalDocuments):
                print("\nRemaining documents: {}".format(totalDocuments - i))

                # print("\nTaking a short break...")
                # time.sleep(20)
                # print("Allright, ready to go...\n")

        print("\n")
        print("*" * 60)
        print("Successfully textracted {} of {} documents".format(successes, totalDocuments))
        print("*" * 60)
        print("\n")


if __name__ == "__main__":
    Textractor().run()
