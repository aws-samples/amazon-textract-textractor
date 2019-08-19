using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Threading.Tasks;
using Amazon.Textract;
using Amazon.Textract.Model;

namespace Dotnet_Core.Services {
	public class TextractTextDetectionService {
		private IAmazonTextract textract;
		public TextractTextDetectionService(IAmazonTextract textract) {
			this.textract = textract;
		}

		public async Task<string> StartDocumentTextDetection(string bucketName, string key) {
			var request = new StartDocumentTextDetectionRequest();
			request.DocumentLocation = new DocumentLocation {
				S3Object = new S3Object {
					Bucket = bucketName,
					Name = key
				}
			};
			var response = await this.textract.StartDocumentTextDetectionAsync(request);
			return response.JobId;
		}

		public async Task<DetectDocumentTextResponse> DetectTextLocal(string localPath) {
			var result = new DetectDocumentTextResponse();

			if(File.Exists(localPath)) {
				var request = new DetectDocumentTextRequest();
				request.Document = new Document {
					Bytes = new MemoryStream(File.ReadAllBytes(localPath))
				};
				return await this.textract.DetectDocumentTextAsync(request);
			}
			Console.WriteLine("File: " + localPath + " doesn't exist");
			return result;
		}

		public void WaitForJobCompletion(string jobId, int delay = 5000) {
			while(!IsJobComplete(jobId)) {
				this.Wait(delay);
			}
		}

		public bool IsJobComplete(string jobId) {
			var response = this.textract.GetDocumentTextDetectionAsync(new GetDocumentTextDetectionRequest {
				JobId = jobId
			});
			response.Wait();
			return !response.Result.JobStatus.Equals("IN_PROGRESS");
		}

		public List<GetDocumentTextDetectionResponse> GetJobResults(string jobId) {
			var result = new List<GetDocumentTextDetectionResponse>();
			var response = this.textract.GetDocumentTextDetectionAsync(new GetDocumentTextDetectionRequest {
				JobId = jobId
			});
			response.Wait();
			result.Add(response.Result);
			var nextToken = response.Result.NextToken;
			while(nextToken != null) {
				this.Wait();
				response = this.textract.GetDocumentTextDetectionAsync(new GetDocumentTextDetectionRequest {
					JobId = jobId,
					NextToken = response.Result.NextToken
				});
				response.Wait();
				result.Add(response.Result);
				nextToken = response.Result.NextToken;
			}
			return result;
		}

		private void Wait(int delay = 5000) {
			Task.Delay(delay).Wait();
			Console.Write(".");
		}

		public async Task<DetectDocumentTextResponse> DetectTextS3(string bucketName, string key) {
			var result = new DetectDocumentTextResponse();
			var s3Object = new S3Object {
				Bucket = bucketName,
				Name = key
			};
			var request = new DetectDocumentTextRequest();
			request.Document = new Document {
				S3Object = s3Object
			};
			return await this.textract.DetectDocumentTextAsync(request);
		}

		private void Print(List<Block> blocks) {
			blocks.ForEach(x => {
				if(x.BlockType.Equals("LINE")) {
					Console.WriteLine(x.Text);
				}
			});
		}

		public void Print(DetectDocumentTextResponse response) {
			if(response != null) {
				this.Print(response.Blocks);
			}
		}

		public void Print(List<GetDocumentTextDetectionResponse> response) {
			if(response != null && response.Count > 0) {
				response.ForEach(r => this.Print(r.Blocks));
			}
		}

		public List<string> GetLines(DetectDocumentTextResponse result) {
			var lines = new List<string>();
			result.Blocks.FindAll(block => block.BlockType == "LINE").ForEach(block => lines.Add(block.Text));
			return lines;
		}
	}
}