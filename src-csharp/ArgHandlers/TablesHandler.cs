using System;
using Amazon.Textract.Model;
using Dotnet_Core.Services;

namespace Dotnet_Core.ArgHandlers {
	internal class TablesHandler {
		private readonly TextractTextAnalysisService textractAnalysisService;

		public TablesHandler(TextractTextAnalysisService textractAnalysisService) {
			this.textractAnalysisService = textractAnalysisService;
		}

		internal void Handle(string bucketName, string formFile) {
			var task = textractAnalysisService.StartDocumentAnalysis(bucketName, formFile, "TABLES");
			var jobId = task.Result;
			textractAnalysisService.WaitForJobCompletion(jobId);
			var results = textractAnalysisService.GetJobResults(jobId);
			var document = new TextractDocument(results);
			document.Pages.ForEach(page => {
				page.Tables.ForEach(table => {
					var r = 0;
					table.Rows.ForEach(row => {
						r++;
						var c = 0;
						row.Cells.ForEach(cell => {
							c++;
							Console.WriteLine("Table [{0}][{1}] = {2}", r, c, cell.Text);
						});
					});
				});
			});
		}
	}
}