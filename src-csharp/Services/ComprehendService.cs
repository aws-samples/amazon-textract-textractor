using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Amazon.Comprehend;
using Amazon.Comprehend.Model;
using Amazon.ComprehendMedical;
using MedicalModel = Amazon.ComprehendMedical.Model;

namespace Dotnet_Core.Services {
	public class ComprehendService {
		private IAmazonComprehend comprehend { get; }
		private IAmazonComprehendMedical comprehendMedical { get; }
		public ComprehendService(IAmazonComprehend comprehend) {
			this.comprehend = comprehend;
		}

		public ComprehendService(IAmazonComprehendMedical comprehend) {
			this.comprehendMedical = comprehend;
		}

		public async Task<DetectedSentiment> DetectSentiment(string languageCode, string text) {
			var task = await this.comprehend.DetectSentimentAsync(new DetectSentimentRequest {
				LanguageCode = languageCode,
				Text = text
			});
			return new DetectedSentiment {
				Sentiment = task.Sentiment,
				Mixed = task.SentimentScore.Mixed,
				Neutral = task.SentimentScore.Neutral,
				Negative = task.SentimentScore.Negative,
				Positive = task.SentimentScore.Positive
			};
		}

		public async Task<List<Entity>> DetectEntities(string languageCode, string text) {
			var task = await this.comprehend.DetectEntitiesAsync(new DetectEntitiesRequest {
				LanguageCode = languageCode,
				Text = text
			});
			return task.Entities;
		}

		public async Task<List<MedicalModel.Entity>> DetectEntities(string text) {
			var task = await this.comprehendMedical.DetectEntitiesAsync(new MedicalModel.DetectEntitiesRequest {
				Text = text
			});
			return task.Entities;
		}

		public class DetectedSentiment {
			public string Sentiment { get; set; }
			public float Mixed { get; set; }
			public float Positive { get; set; }
			public float Neutral { get; set; }
			public float Negative { get; set; }

			public override string ToString() {
				return string.Format("Sentiment: {0}, Score: [Mixed: {1}, Positive: {2}, Negative: {3}, Neutral: {4}]", this.Sentiment, this.Mixed, this.Positive, this.Negative, this.Neutral);
			}

		}
	}
}
