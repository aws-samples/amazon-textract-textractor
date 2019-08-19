using System;
using Dotnet_Core.Services;

namespace Dotnet_Core.ArgHandlers {
	internal class DetectTextS3Handler {
		private readonly TextractTextDetectionService textractTextService;

		public DetectTextS3Handler(TextractTextDetectionService textractTextService) {
			this.textractTextService = textractTextService;
		}

		internal void Handle(string bucketName, string s3File) {
			var s3Task = textractTextService.DetectTextS3(bucketName, s3File);
			s3Task.Wait();
			textractTextService.Print(s3Task.Result);
		}
	}
}