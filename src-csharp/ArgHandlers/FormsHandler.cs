using System;
using Amazon.Textract.Model;
using Dotnet_Core.Services;

namespace Dotnet_Core.ArgHandlers {
	internal class FormsHandler {
		private readonly TextractTextAnalysisService textractAnalysisService;
		public FormsHandler(TextractTextAnalysisService textractAnalysisService) {
			this.textractAnalysisService = textractAnalysisService;
		}

		internal void Handle(string bucketName, string formFile) {
			var task = textractAnalysisService.StartDocumentAnalysis(bucketName, formFile, "FORMS");
			var jobId = task.Result;
			textractAnalysisService.WaitForJobCompletion(jobId);
			var results = textractAnalysisService.GetJobResults(jobId);
			var document = new TextractDocument(results);
			document.Pages.ForEach(page => {
				page.Form.Fields.ForEach(f => {
					Console.WriteLine("Key: {0}, Value {1}", f.Key, f.Value);
				});
				Console.WriteLine("Get Field by Key:");
				var key = "Phone Number:";
				var field = page.Form.GetFieldByKey(key);
				if(field != null) {
					Console.WriteLine("Key: {0}, Value: {1}", field.Key, field.Value);
				}
			});
		}
	}
}