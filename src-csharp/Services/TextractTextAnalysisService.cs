using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Amazon.Textract;
using Amazon.Textract.Model;

namespace Dotnet_Core.Services {
	public class TextractTextAnalysisService {
		private IAmazonTextract textract;
		public TextractTextAnalysisService(IAmazonTextract textract) {
			this.textract = textract;
		}
		public GetDocumentAnalysisResponse GetJobResults(string jobId) {
			var response = this.textract.GetDocumentAnalysisAsync(new GetDocumentAnalysisRequest {
				JobId = jobId
			});
			response.Wait();
			return response.Result;
		}

		public bool IsJobComplete(string jobId) {
			var response = this.textract.GetDocumentAnalysisAsync(new GetDocumentAnalysisRequest {
				JobId = jobId
			});
			response.Wait();
			return !response.Result.JobStatus.Equals("IN_PROGRESS");
		}

		public async Task<string> StartDocumentAnalysis(string bucketName, string key, string featureType) {
			var request = new StartDocumentAnalysisRequest();
			var s3Object = new S3Object {
				Bucket = bucketName,
				Name = key
			};
			request.DocumentLocation = new DocumentLocation {
				S3Object = s3Object
			};
			request.FeatureTypes = new List<string> { featureType };
			var response = await this.textract.StartDocumentAnalysisAsync(request);
			return response.JobId;
		}

		public void WaitForJobCompletion(string jobId, int delay = 5000) {
			while(!IsJobComplete(jobId)) {
				this.Wait(delay);
			}
		}

		private void Wait(int delay = 5000) {
			Task.Delay(delay).Wait();
			Console.Write(".");
		}

		public void PrintDebug(GetDocumentAnalysisResponse response) {
			response.Blocks.ForEach(y => {
				Console.WriteLine("<block>");
				Console.WriteLine(y.Id + ":" + y.BlockType + ":" + y.Text);
				if(y.BlockType == "KEY_VALUE_SET") {
					Console.WriteLine(" <KEY_VALUE_SET>");
					PrintBlock(y);
					Console.WriteLine(" </KEY_VALUE_SET>");
				} else if(y.BlockType == "TABLE") {
					Console.WriteLine(" <TABLE>");
					PrintBlock(y);
					Console.WriteLine(" </TABLE>");
				} else if(y.BlockType == "CELL") {
					Console.WriteLine(" <CELL>");
					PrintBlock(y);
					Console.WriteLine(" </CELL>");
				}
				Console.WriteLine("</block>");
			});
		}
		private void PrintBlock(Block block) {
			Console.WriteLine("  <entity>");
			block.EntityTypes.ForEach(z => Console.WriteLine("   " + z));
			Console.WriteLine("  </entity>");
			block.Relationships.ForEach(z => {
				Console.WriteLine("  <relation>");
				Console.WriteLine("   " + z.Type);
				Console.WriteLine("   <id>");
				z.Ids.ForEach(a => Console.WriteLine("    " + a));
				Console.WriteLine("   </id>");
				Console.WriteLine("  </relation>");
			});
		}
	}
}