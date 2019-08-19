using System.Threading.Tasks;
using Amazon.Translate;
using Amazon.Translate.Model;

namespace Dotnet_Core.Services {
	public class TranslateService {
		private IAmazonTranslate translate;
		public TranslateService(IAmazonTranslate translate) {
			this.translate = translate;
		}

		public async Task<TranslateTextResponse> TranslateText(string text, string sourceLanguage, string targetLanguage) {
			var request = new TranslateTextRequest {
				SourceLanguageCode = sourceLanguage,
				TargetLanguageCode = targetLanguage,
				Text = text
			};

			return await this.translate.TranslateTextAsync(request);
		}
	}
}