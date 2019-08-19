using System;
using Dotnet_Core.Services;

namespace Dotnet_Core.ArgHandlers {
	internal class PdfTextHandler {
		private readonly TextractTextDetectionService textractTextService;

		public PdfTextHandler(TextractTextDetectionService textractTextService) {
			this.textractTextService = textractTextService;
		}

		internal void Handle(string bucketName, string pdfFile) {
			var task = textractTextService.StartDocumentTextDetection(bucketName, pdfFile);
			var jobId = task.Result;
			textractTextService.WaitForJobCompletion(jobId);
			textractTextService.Print(textractTextService.GetJobResults(jobId));
		}
	}
}