using System;
using System.Text;
using Dotnet_Core.Services;

namespace Dotnet_Core.ArgHandlers {
	internal class TranslateHandler {
		private readonly TextractTextDetectionService textractTextService;
		private readonly TranslateService translateService;

		public TranslateHandler(TextractTextDetectionService textractTextService, TranslateService translateService) {
			this.textractTextService = textractTextService;
			this.translateService = translateService;
		}

		internal void Handle(string bucketName, string s3File) {
			var detectTextTask = textractTextService.DetectTextS3(bucketName, s3File);
			detectTextTask.Wait();
			var blocks = detectTextTask.Result.Blocks;
			var sourceText = new StringBuilder();
			blocks.ForEach(x => {
				if(x.BlockType == "LINE") {
					sourceText.AppendLine(x.Text);
				}
			});
			Console.WriteLine(sourceText.ToString());
			var translateTask = translateService.TranslateText(sourceText.ToString(), "en", "de");
			translateTask.Wait();
			Console.WriteLine(translateTask.Result.TranslatedText);
		}
	}
}