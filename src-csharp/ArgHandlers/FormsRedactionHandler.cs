using System;
using System.Drawing;
using System.IO;
using Amazon.Textract.Model;
using Dotnet_Core.Services;

namespace Dotnet_Core.ArgHandlers {
	internal class FormsRedactionHandler {
		private readonly TextractTextAnalysisService textractAnalysisService;

		public FormsRedactionHandler(TextractTextAnalysisService textractAnalysisService) {
			this.textractAnalysisService = textractAnalysisService;
		}

		internal void Handle(string bucketName, string formFile, string localFolder, string localFile) {
			var task = textractAnalysisService.StartDocumentAnalysis(bucketName, formFile, "FORMS");
			var jobId = task.Result;
			textractAnalysisService.WaitForJobCompletion(jobId);
			var results = textractAnalysisService.GetJobResults(jobId);

			var redactableImage = Path.Join(localFolder, "redacted-" + formFile);
			if(File.Exists(redactableImage))
				File.Delete(redactableImage);
			File.Copy(localFile, redactableImage);
			var image = Image.FromFile(redactableImage);
			var graphics = Graphics.FromImage(image);
			var height = image.Height;
			var width = image.Width;
			Console.WriteLine("image dimensions: {0}x{1}", width, height);

			var document = new TextractDocument(results);
			document.Pages.ForEach(page => {
				page.Form.Fields.ForEach(field => {
					if(field.Key.Text.ToLower().Contains("address")) {
						Console.WriteLine("Redacting Key: {0}, Value: {1}", field.Key.Text, field.Value.Text);
						var bb = field.Value.Geometry.BoundingBox;
						Console.WriteLine(bb);
						var x1 = bb.Left * width;
						var y1 = bb.Top * height - 2;
						var x2 = bb.Width * width + 2;
						var y2 = bb.Height * height + 2;

						Console.WriteLine("x1: {0}, x2: {1}, y1: {2}, y2: {3}", x1, x2, y1, y2);
						graphics.FillRectangle(new SolidBrush(Color.Black), x1, y1, x2, y2);
						graphics.Save();
						image.Save(redactableImage);
						Console.WriteLine("redacted image saved at: {0}", redactableImage);
					}
				});
			});
		}
	}
}