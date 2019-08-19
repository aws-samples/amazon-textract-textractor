using System;
using Dotnet_Core.Services;

namespace Dotnet_Core.ArgHandlers {
	internal class NlpComprehendMedicalHandler {
		private readonly TextractTextDetectionService textractTextService;
		private readonly ComprehendService comprehendMedicalService;

		public NlpComprehendMedicalHandler(TextractTextDetectionService textractTextService, ComprehendService comprehendMedicalService) {
			this.textractTextService = textractTextService;
			this.comprehendMedicalService = comprehendMedicalService;
		}

		internal void Handle(string medicalFile) {
			var localTask = textractTextService.DetectTextLocal(medicalFile);
			localTask.Wait();
			var result = localTask.Result;
			var lineItems = textractTextService.GetLines(result);
			var medicalTask = comprehendMedicalService.DetectEntities(string.Join("", lineItems));
			medicalTask.Wait();
			medicalTask.Result.ForEach(entity => {
				Console.WriteLine("Text: [{0}], Type: [{1}], Category: [{2}]", entity.Text, entity.Type, entity.Category);
				entity.Traits.ForEach(trait => {
					Console.WriteLine(" Trait: [{0}], Score: [{1}]", trait.Name, trait.Score);
				});
			});
		}
	}
}