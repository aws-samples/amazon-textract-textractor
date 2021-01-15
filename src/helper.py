import boto3
from botocore.client import Config
import os
import csv


class AwsHelper:
    def getClient(self, name, awsRegion):
        config = Config(retries=dict(max_attempts=30))
        return boto3.client(name, region_name=awsRegion, config=config)


class S3Helper:
    @staticmethod
    def getS3BucketRegion(bucketName):
        client = boto3.client('s3')
        response = client.get_bucket_location(Bucket=bucketName)
        awsRegion = response['LocationConstraint']
        return awsRegion

    @staticmethod
    def checkObjectExists(awsRegion, bucketName, key):
        s3client = AwsHelper().getClient("s3", awsRegion)
        try:
            meta = s3client.head_object(
                Bucket=bucketName,
                Key=key,
            )
            if meta.get("DeleteMarker", False):
                return False
            else:
                return True
        # At time of writing, boto3 API doc says that head_object should raise
        # NoSuchKey but current behavior is generic ClientError per issue at:
        # https://github.com/boto/boto3/issues/2442
        except s3client.exceptions.NoSuchKey:
            return False
        except s3client.exceptions.ClientError as e:
            if e.response.get("Error", {}).get("Code") == "NoSuchKey":
                return False
            else:
                raise e

    @staticmethod
    def getFileNames(awsRegion, bucketName, prefix, maxPages,
                     allowedFileTypes):

        files = []

        currentPage = 1
        hasMoreContent = True
        continuationToken = None

        s3client = AwsHelper().getClient('s3', awsRegion)

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

            # "Contents" may be missing if KeyCount is 0 (no objects)
            if listObjectsResponse["KeyCount"] == 0:
                continue
            for doc in listObjectsResponse['Contents']:
                docName = doc['Key']
                docExt = FileHelper.getFileExtension(docName)
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
    def getFileExtension(fileName):
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
    def checkFileExists(path):
        return os.path.isfile(path)

    @staticmethod
    def ensureFolder(path):
        return os.makedirs(path, exist_ok=True)

    @staticmethod
    def getFileNames(path, allowedLocalFileTypes):
        results = []
        for currpath, dirs, files in os.walk(path):
            for file in files:
                ext = FileHelper.getFileExtension(file)
                if (ext.lower() in allowedLocalFileTypes):
                    results.append(os.path.join(currpath, file))
        return results

    @staticmethod
    def mapSubFolder(fromBase, path, toBase):
        """Map directories of `path` below `fromBase` to `toBase`

        Parameters
        ----------
        fromBase : Union[str, None]
            Base folder within which `path` exists. If None (unknown), the
            function will just return `toBase`. E.g. 'a/'
        path : str
            File path of interest. E.g. 'a/b/c/d.jpg'
        toBase : str
            Base output folder that `path` is being mapped to, relative to
            `fromBase`. E.g. 'out/'

        Returns
        -------
        folder : str
            Output subfolder, including `toBase` but excluding filename. E.g.
            'out/b/c'
        """
        if fromBase is None:
            return toBase
        pathDir = os.path.dirname(path)
        if pathDir == "":
            return toBase
        # Otherwise calculate subfolders between fromBase->path:
        subfolders = os.path.relpath(pathDir, start=fromBase)
        # And join to `toBase`, normalizing because subfolders may be the
        # special '.' same folder link and we don't want to confuse downstream
        # logic with paths like 'out/./img.jpg':
        return os.path.normpath(os.path.join(toBase, subfolders))

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
