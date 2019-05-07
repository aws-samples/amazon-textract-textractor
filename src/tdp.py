import os
import time
from helper import AwsHelper, FileHelper

class Input:

    def __init__(self):
        self.bucketName = ""
        self.documentPath = ""
        self.awsRegion = "us-east-1"
        self.detectText = False
        self.detectForms = False
        self.detectTables = False

        self.isLocalDocument = False
        self.documentType = ""

    def __str__(self):
        s = "---------------------------------------------\n"
        if(not self.isLocalDocument):
            s = s + "Bucket Name: {}\n".format(self.bucketName)
        s = s + "Document: {}\n".format(self.documentPath)
        s = s + "Text: {}\n".format(self.detectText)
        s = s + "Form: {}\n".format(self.detectForms)
        s = s + "Table: {}\n".format(self.detectTables)
        s = s + "AWS Region: {}".format(self.awsRegion)
        s = s + "---------------------------------------------\n"

class ImageProcessor:
    def __init__(self, inputParameters):
        ''' Constructor. '''
        self.inputParameters = inputParameters

    def _callTextract(self):
        textract = AwsHelper().getClient('textract', self.inputParameters.awsRegion)
        if(not self.inputParameters.detectForms and not self.inputParameters.detectTables):
            if(self.inputParameters.isLocalDocument):
                with open(self.inputParameters.documentPath, 'rb') as document:
                    imageData = document.read()
                    imageBytes = bytearray(imageData)

                response = textract.detect_document_text(Document={'Bytes': imageBytes})
            else:
                response = textract.detect_document_text(
                    Document={
                        'S3Object': {
                            'Bucket': self.inputParameters.bucketName,
                            'Name': self.inputParameters.documentPath
                        }
                    }
                )
        else:
            features  = []
            if(self.inputParameters.detectTables):
                features.append("TABLES")
            if(self.inputParameters.detectForms):
                features.append("FORMS")

            if(self.inputParameters.isLocalDocument):
                with open(self.inputParameters.documentPath, 'rb') as document:
                    imageData = document.read()
                    imageBytes = bytearray(imageData)

                response = textract.analyze_document(Document={'Bytes': imageBytes} , FeatureTypes=features)
            else:
                response = textract.analyze_document(
                    Document={
                        'S3Object': {
                            'Bucket': self.inputParameters.bucketName,
                            'Name': self.inputParameters.documentPath
                        }
                    },
                    FeatureTypes=features
                )

        return response

    def run(self):
        response = self._callTextract()
        return response

class PdfProcessor:
    def __init__(self, inputParameters):
        self.inputParameters = inputParameters

    def _startJob(self):
        response = None
        client = AwsHelper().getClient('textract', self.inputParameters.awsRegion)
        if(not self.inputParameters.detectForms and not self.inputParameters.detectTables):
            response = client.start_document_text_detection(
            DocumentLocation={
                'S3Object': {
                    'Bucket': self.inputParameters.bucketName,
                    'Name': self.inputParameters.documentPath
                }
            })
        else:
            features  = []
            if(self.inputParameters.detectTables):
                features.append("TABLES")
            if(self.inputParameters.detectForms):
                features.append("FORMS")

            response = client.start_document_analysis(
            DocumentLocation={
                'S3Object': {
                    'Bucket': self.inputParameters.bucketName,
                    'Name': self.inputParameters.documentPath
                }
            },
            FeatureTypes=features
            )

        return response["JobId"]

    def _isJobComplete(self, jobId):
        time.sleep(5)
        client = AwsHelper().getClient('textract', self.inputParameters.awsRegion)
        if(not self.inputParameters.detectForms and not self.inputParameters.detectTables):
            response = client.get_document_text_detection(JobId=jobId)
        else:
            response = client.get_document_analysis(JobId=jobId)
        status = response["JobStatus"]
        print(status)

        while(status == "IN_PROGRESS"):
            time.sleep(5)
            if(not self.inputParameters.detectForms and not self.inputParameters.detectTables):
                response = client.get_document_text_detection(JobId=jobId)
            else:
                response = client.get_document_analysis(JobId=jobId)
            status = response["JobStatus"]
            print(status)

        return status

    def _getJobResults(self, jobId):

        pages = []

        time.sleep(5)

        client = AwsHelper().getClient('textract', self.inputParameters.awsRegion)
        if(not self.inputParameters.detectForms and not self.inputParameters.detectTables):
            response = client.get_document_text_detection(JobId=jobId)
        else:
            response = client.get_document_analysis(JobId=jobId)
        pages.append(response)
        print("Resultset page recieved: {}".format(len(pages)))
        nextToken = None
        if('NextToken' in response):
            nextToken = response['NextToken']
            #print("Next token: {}".format(nextToken))

        while(nextToken):
            time.sleep(5)

            if(not self.inputParameters.detectForms and not self.inputParameters.detectTables):
                response = client.get_document_text_detection(JobId=jobId, NextToken=nextToken)
            else:
                response = client.get_document_analysis(JobId=jobId, NextToken=nextToken)

            pages.append(response)
            print("Resultset page recieved: {}".format(len(pages)))
            nextToken = None
            if('NextToken' in response):
                nextToken = response['NextToken']
                #print("Next token: {}".format(nextToken))

            #if(len(pages) > 20):
            #    break

        return pages

    def run(self):
        jobId = self._startJob()
        print("Started Asyc Job with Id: {}".format(jobId))
        status = self._isJobComplete(jobId)
        if(status == "SUCCEEDED"):
            responsePages = self._getJobResults(jobId)
            return responsePages

class DocumentProcessor:

    def __init__(self, bucketName, documentPath, awsRegion, detectText, detectForms, detectTables):

        ip = Input()
        if(bucketName):
            ip.bucketName = bucketName
        if(documentPath):
            ip.documentPath = documentPath
        if(awsRegion):
            ip.awsRegion = awsRegion
        if(detectText):
            ip.detectText = detectText
        if(detectForms):
            ip.detectForms = detectForms
        if(detectTables):
            ip.detectTables = detectTables

        if(not ip.bucketName and not ip.documentPath):
            raise Exception("Document is required.")

        if(ip.bucketName):
            ip.isLocalDocument = False
        else:
            ip.isLocalDocument = True

        ext = FileHelper.getFileExtenstion(ip.documentPath).lower()
        if(ext == "pdf"):
            ip.documentType = "PDF"
        elif(ext == "jpg" or ext == "jpeg" or ext == "png"):
            ip.documentType = "IMAGE"
        else:
            raise Exception("Document should be jpg/jpeg, png or pdf.")

        if(ip.documentType == "PDF" and ip.isLocalDocument):
            raise Exception("PDF must be in S3 bucket.")

        if(ip.detectText == False and ip.detectForms == False and ip.detectTables == False):
            raise Exception("Select at least one option to extract text, form or table")

        self.inputParameters = ip

    def run(self):

        print("Calling Textract...")

        # Call and Get results from Textract
        if(self.inputParameters.documentType == "IMAGE"):
            ip = ImageProcessor(self.inputParameters)
            response = ip.run()
            responsePages = []
            responsePages.append(response)
            self.responsePages = responsePages
        else:
            pp = PdfProcessor(self.inputParameters)
            responsePages = pp.run()
            self.responsePages = responsePages

        return self.responsePages
