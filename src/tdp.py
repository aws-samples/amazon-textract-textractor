import time
from helper import AwsHelper, FileHelper, S3Helper
from textract_features import TEXTRACT_ASYNC_ONLY_SUFFIXES, TEXTRACT_FEATURES, TEXTRACT_SYNC_SUFFIXES, TEXTRACT_ANALYZE_FEATURES


class ImageProcessor:
    def __init__(self, s3_bucket, document: str, local: bool, region: str,
                 textract_features: "list[TEXTRACT_FEATURES]"):
        ''' Constructor. '''
        self.s3_bucket = s3_bucket
        self.region = region
        self.document = document
        self.textract_features = textract_features
        self.local = local
        self.analyze_features = [
            x.name for x in self.textract_features
            if x in TEXTRACT_ANALYZE_FEATURES
        ]

    def _callTextract(self):
        textract = AwsHelper.getClient('textract', awsRegion=self.region)
        if not self.analyze_features:
            if (self.local):
                with open(self.document, 'rb') as document:
                    imageData = document.read()
                    imageBytes = bytearray(imageData)

                response = textract.detect_document_text(
                    Document={'Bytes': imageBytes})
            else:
                response = textract.detect_document_text(Document={
                    'S3Object': {
                        'Bucket': self.s3_bucket,
                        'Name': self.document
                    }
                })
        else:
            if (self.local):
                with open(self.document, 'rb') as document:
                    imageData = document.read()
                    imageBytes = bytearray(imageData)

                response = textract.analyze_document(
                    Document={'Bytes': imageBytes},
                    FeatureTypes=self.analyze_features)
            else:
                response = textract.analyze_document(
                    Document={
                        'S3Object': {
                            'Bucket': self.s3_bucket,
                            'Name': self.document
                        }
                    },
                    FeatureTypes=self.analyze_features)

        return response

    def run(self):
        response = self._callTextract()
        return response


class PdfProcessor:
    def __init__(self, s3_bucket, document: str, local: bool, region: str,
                 textract_features: "list[TEXTRACT_FEATURES]"):
        ''' Constructor. '''
        self.s3_bucket = s3_bucket
        self.region = region
        self.document = document
        self.textract_features = textract_features
        self.local = local
        self.analyze_features = [
            x.name for x in self.textract_features
            if x in TEXTRACT_ANALYZE_FEATURES
        ]

    def _startJob(self):
        response = None
        client = AwsHelper.getClient('textract', awsRegion=self.region)
        if not self.analyze_features:
            response = client.start_document_text_detection(DocumentLocation={
                'S3Object': {
                    'Bucket': self.s3_bucket,
                    'Name': self.document
                }
            })
        else:
            response = client.start_document_analysis(
                DocumentLocation={
                    'S3Object': {
                        'Bucket': self.s3_bucket,
                        'Name': self.document
                    }
                },
                FeatureTypes=self.analyze_features)

        return response["JobId"]

    def _isJobComplete(self, jobId):
        time.sleep(5)
        client = AwsHelper.getClient('textract', self.region)
        if not self.analyze_features:
            response = client.get_document_text_detection(JobId=jobId)
        else:
            response = client.get_document_analysis(JobId=jobId)
        status = response["JobStatus"]
        print("Job Status: {}".format(status))

        while (status == "IN_PROGRESS"):
            time.sleep(5)
            if not self.analyze_features:
                response = client.get_document_text_detection(JobId=jobId)
            else:
                response = client.get_document_analysis(JobId=jobId)
            status = response["JobStatus"]
            print("Job Status: {}".format(status))

        return status

    def _getJobResults(self, jobId):
        pages = []

        #time.sleep(5)

        client = AwsHelper.getClient('textract', self.region)
        if not self.analyze_features:
            response = client.get_document_text_detection(JobId=jobId)
        else:
            response = client.get_document_analysis(JobId=jobId)
        pages.append(response)
        print("Resultset page recieved: {}".format(len(pages)))
        nextToken = None
        if ('NextToken' in response):
            nextToken = response['NextToken']
            #print("Next token: {}".format(nextToken))

        while (nextToken):
            #time.sleep(5)

            if not self.analyze_features:
                response = client.get_document_text_detection(
                    JobId=jobId, NextToken=nextToken)
            else:
                response = client.get_document_analysis(JobId=jobId,
                                                        NextToken=nextToken)

            pages.append(response)
            print("Resultset page recieved: {}".format(len(pages)))
            nextToken = None
            if ('NextToken' in response):
                nextToken = response['NextToken']
                #print("Next token: {}".format(nextToken))

            #if(len(pages) > 20):
            #    break

        return pages

    def run(self):
        jobId = self._startJob()
        print("Started Asyc Job with Id: {}".format(jobId))
        status = self._isJobComplete(jobId)
        if (status == "SUCCEEDED"):
            responsePages = self._getJobResults(jobId)
            return responsePages


class DocumentProcessor:
    def __init__(self, bucketName, documentPath, awsRegion,
                 textract_features: "list[TEXTRACT_FEATURES]"):

        self.s3_bucket = bucketName
        self.document = documentPath
        self.region = awsRegion
        self.textract_features = textract_features
        self.local = not S3Helper.path_is_s3(documentPath)
        _, suffix = FileHelper.getFileNameAndExtension(documentPath)
        if suffix in TEXTRACT_SYNC_SUFFIXES:
            self.document_type = "IMAGE"
        elif suffix in TEXTRACT_ASYNC_ONLY_SUFFIXES:
            self.document_type = "PDF"
        else:
            return ValueError("Unsupported suffix")

    def run(self):

        print("Calling Textract...")

        # Call and Get results from Textract
        if (self.document_type == "IMAGE"):
            ip = ImageProcessor(s3_bucket=self.s3_bucket,
                                document=self.document,
                                local=self.local,
                                region=self.region,
                                textract_features=self.textract_features)
            response = ip.run()
            responsePages = []
            responsePages.append(response)
            self.responsePages = responsePages
        else:
            pp = PdfProcessor(s3_bucket=self.s3_bucket,
                              document=self.document,
                              local=self.local,
                              region=self.region,
                              textract_features=self.textract_features)
            responsePages = pp.run()
            self.responsePages = responsePages

        return self.responsePages
