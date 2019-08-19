using System;
using Dotnet_Core.Services;

namespace Dotnet_Core.ArgHandlers {
	internal class NlpComprehendHandler {
		private readonly TextractTextDetectionService textractTextService;
		private readonly ComprehendService comprehendService;

		public NlpComprehendHandler(TextractTextDetectionService textractTextService, ComprehendService comprehendService) {
			this.textractTextService = textractTextService;
			this.comprehendService = comprehendService;
		}

		internal void Handle(string localFile) {
			var localTask = textractTextService.DetectTextLocal(localFile);
			localTask.Wait();
			var result = localTask.Result;
			var lineItems = textractTextService.GetLines(result);
			var detectSentimentTask = comprehendService.DetectSentiment("en", string.Join("", lineItems));
			detectSentimentTask.Wait();
			Console.WriteLine(detectSentimentTask.Result);
			var detectEntitiesTask = comprehendService.DetectEntities("en", string.Join("", lineItems));
			detectEntitiesTask.Wait();
			detectEntitiesTask.Result.ForEach(entity => {
				Console.WriteLine("{0}:{1}:{2}", entity.Text, entity.Score, entity.Type);
			});
		}
	}
}