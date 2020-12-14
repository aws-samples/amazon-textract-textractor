import boto3
from botocore.client import Config
import os
import csv
from urllib.parse import urlparse

from textract_features import TEXTRACT_SUFFIXES


class AwsHelper:
    @staticmethod
    def getClient(name, awsRegion):
        config = Config(retries=dict(max_attempts=30))
        return boto3.client(name, region_name=awsRegion, config=config)


class S3Helper:
    @staticmethod
    def path_is_s3(path: str) -> bool:
        if not path:
            raise ValueError("no path passed to function")
        return path.lower().startswith("s3://")

    @staticmethod
    def getS3BucketRegion(bucketName):
        client = boto3.client('s3')
        response = client.get_bucket_location(Bucket=bucketName)
        awsRegion = response['LocationConstraint']
        return awsRegion

    @staticmethod
    def split_bucket_and_key(s3_object):
        """return s3_bucket, s3_key from string"""
        o = urlparse(s3_object)
        return o.netloc, o.path[1:]

    @staticmethod
    def get_s3_object_keys(s3_object: str, allowedFileTypes=TEXTRACT_SUFFIXES):
        """returns the documents as list of string. Either all document-keys in path (when str ends in /) or the document key
           for the allowed file types [jpg, jpeg, png, pdf]
        """
        if not s3_object or not S3Helper.path_is_s3(s3_object):
            raise ValueError(
                "no s3_object or missing s3:// : '{}'".format(s3_object))
        s3_bucket = None
        documents = []
        awsRegion = 'us-east-1'
        s3_bucket, s3_key = S3Helper.split_bucket_and_key(s3_object)
        ar = S3Helper.getS3BucketRegion(s3_bucket)
        if (ar):
            awsRegion = ar

        if (s3_key.endswith("/")):
            documents = S3Helper.getFileNames(awsRegion, s3_bucket, s3_key, 1,
                                              allowedFileTypes)
        else:
            documents.append(s3_key)
        return documents

    @staticmethod
    def getFileNames(awsRegion, bucketName, prefix, maxPages,
                     allowedFileTypes):

        files = []

        currentPage = 1
        hasMoreContent = True
        continuationToken = None

        s3client = AwsHelper.getClient('s3', awsRegion)

        while (hasMoreContent and currentPage <= maxPages):
            if (continuationToken):
                listObjectsResponse = s3client.list_objects_v2(
                    Bucket=bucketName,
                    Prefix=prefix,
                    ContinuationToken=continuationToken)
            else:
                listObjectsResponse = s3client.list_objects_v2(
                    Bucket=bucketName, Prefix=prefix)

            if (listObjectsResponse['IsTruncated']):
                continuationToken = listObjectsResponse[
                    'NextContinuationToken']
            else:
                hasMoreContent = False

            for doc in listObjectsResponse['Contents']:
                docName = doc['Key']
                docExt = FileHelper.getFileExtenstion(docName)
                docExtLower = docExt.lower()
                if (docExtLower in allowedFileTypes):
                    files.append(docName)

        return files


class FileHelper:
    @staticmethod
    def getFileNameAndExtension(filePath):
        basename = os.path.basename(filePath)
        dn, dext = os.path.splitext(basename)
        return (dn, dext[1:])

    @staticmethod
    def getFileName(fileName):
        basename = os.path.basename(fileName)
        dn, dext = os.path.splitext(basename)
        return dn

    @staticmethod
    def getFileExtenstion(fileName):
        basename = os.path.basename(fileName)
        dn, dext = os.path.splitext(basename)
        return dext[1:]

    @staticmethod
    def readFile(fileName):
        with open(fileName, 'r') as document:
            return document.read()

    @staticmethod
    def writeToFile(fileName, content):
        with open(fileName, 'w') as document:
            document.write(content)

    @staticmethod
    def writeToFileWithMode(fileName, content, mode):
        with open(fileName, mode) as document:
            document.write(content)

    @staticmethod
    def getFilesInFolder(path, fileTypes):
        for file in os.listdir(path):
            if os.path.isfile(os.path.join(path, file)):
                ext = FileHelper.getFileExtenstion(file)
                if (ext.lower() in fileTypes):
                    yield file

    @staticmethod
    def getFileNames(path, allowedLocalFileTypes):
        files = []

        for file in FileHelper.getFilesInFolder(path, allowedLocalFileTypes):
            files.append(path + file)

        return files

    @staticmethod
    def writeCSV(fileName, fieldNames, csvData):
        with open(fileName, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldNames)
            writer.writeheader()

            for item in csvData:
                i = 0
                row = {}
                for value in item:
                    row[fieldNames[i]] = value
                    i = i + 1
                writer.writerow(row)

    @staticmethod
    def writeCSVRaw(fileName, csvData):
        with open(fileName, 'w') as csv_file:
            writer = csv.writer(csv_file)
            for item in csvData:
                writer.writerow(item)
