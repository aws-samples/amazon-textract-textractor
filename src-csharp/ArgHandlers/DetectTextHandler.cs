using System;
using Dotnet_Core.Services;

namespace Dotnet_Core.ArgHandlers {
	internal class DetectTextHandler {
		private readonly TextractTextDetectionService textractTextService;

		public DetectTextHandler(TextractTextDetectionService textractTextService) {
			this.textractTextService = textractTextService;
		}

		internal void Handle(string localFile) {
			var localTask = textractTextService.DetectTextLocal(localFile);
			localTask.Wait();
			textractTextService.Print(localTask.Result);
		}
	}
}