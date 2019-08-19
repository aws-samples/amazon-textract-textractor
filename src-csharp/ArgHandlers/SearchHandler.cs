using System;
using Amazon.Textract.Model;
using Dotnet_Core.Services;

namespace Dotnet_Core.ArgHandlers {
	internal class SearchHandler {
		private readonly TextractTextDetectionService textractTextService;
		private readonly ElasticSearchService elasticSearchService;

		public SearchHandler(TextractTextDetectionService textractTextService, ElasticSearchService elasticSearchService) {
			this.textractTextService = textractTextService;
			this.elasticSearchService = elasticSearchService;
		}

		internal void Handle(string bucketName, string s3File) {
			var detectTextTask = textractTextService.DetectTextS3(bucketName, s3File);
			detectTextTask.Wait();
			var result = detectTextTask.Result;
			textractTextService.Print(result);
			elasticSearchService.Index<DetectDocumentTextResponse>(result, "sample-index");
			Console.WriteLine("Index complete");
		}
	}
}