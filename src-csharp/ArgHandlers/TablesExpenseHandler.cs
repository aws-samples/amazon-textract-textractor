using System;
using System.Collections.Generic;
using System.Text;
using Amazon.Textract.Model;
using Dotnet_Core.Services;

namespace Dotnet_Core.ArgHandlers {
	internal class TablesExpenseHandler {
		private readonly TextractTextAnalysisService textractAnalysisService;

		public TablesExpenseHandler(TextractTextAnalysisService textractAnalysisService) {
			this.textractAnalysisService = textractAnalysisService;
		}

		internal void Handle(string bucketName, string expenseFile) {
			var task = textractAnalysisService.StartDocumentAnalysis(bucketName, expenseFile, "TABLES");
			var jobId = task.Result;
			textractAnalysisService.WaitForJobCompletion(jobId);
			var results = textractAnalysisService.GetJobResults(jobId);
			var warnings = new StringBuilder();
			float expense;
			var lineItem = new List<string>();
			var document = new TextractDocument(results);
			document.Pages.ForEach(page => {
				page.Tables.ForEach(table => {
					var r = 0;
					table.Rows.ForEach(row => {
						r++;
						var itemName = string.Empty;
						var c = 0;
						row.Cells.ForEach(cell => {
							c++;
							Console.WriteLine("Table [{0}][{1}] = {2}", r, c, cell.Text);
							if(c == 1) {
								itemName = cell.Text;
							} else if(c == 5 && float.TryParse(cell.Text, out expense)) {
								if(expense > 100) {
									warnings.AppendFormat("{0} is greater than $100{1}", itemName, Environment.NewLine);
								}
							}
						});
					});
				});
			});
			Console.WriteLine(string.Format("{0}===Warnings==={0}{1}===", Environment.NewLine, warnings));
		}
	}
}