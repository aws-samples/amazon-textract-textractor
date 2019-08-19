using System;
using Amazon.Textract;
using Amazon.Translate;
using Microsoft.Extensions.Configuration;
using Amazon.Comprehend;
using Amazon.ComprehendMedical;
using Dotnet_Core.Services;
using Dotnet_Core.ArgHandlers;

namespace Dotnet_Core {
	partial class Program {

		const string BucketName = "textract-console-us-west-2-d92b0df4-a50a-4203-b070-044c3ee7fe83";
		const string LocalEmploymentFile = "test-files/employmentapp.png";
		const string LocalSimpleFile = "test-files/simple-document-image.jpg";
		const string LocalMedicalFile = "test-files/medical-notes.png";
		const string LocalFolder = "test-files";
		const string S3File = "simple-document-image.jpg";
		const string TwoColumnImage = "two-column-image.jpg";
		const string PdfFile = "Amazon-Textract-Pdf.pdf";
		const string FormFile = "employmentapp.png";
		const string ExpenseFile = "expense.png";
		const string ElasticSearchEndpoint = "https://search-textract-sample-hvthzep6bedgfdj6oxeng5jtmi.us-west-2.es.amazonaws.com";
		const string ElasticSearchDomainName = "textract-sample";

		static void Main(string[] args) {
			if(args.Length == 0) {
				Console.WriteLine(HelpText);
				return;
			}

			var firstArg = args[0];

			var builder = new ConfigurationBuilder()
				.SetBasePath(Environment.CurrentDirectory)
				.AddJsonFile("appsettings.json", optional: false, reloadOnChange: true)
				.AddEnvironmentVariables()
				.Build();
			var awsOptions = builder.GetAWSOptions();
			Console.WriteLine(awsOptions.Profile + ":" + awsOptions.ProfilesLocation + ": " + awsOptions.Region.DisplayName);
			var textractTextService = new TextractTextDetectionService(awsOptions.CreateServiceClient<IAmazonTextract>());
			var textractAnalysisService = new TextractTextAnalysisService(awsOptions.CreateServiceClient<IAmazonTextract>());
			var translateService = new TranslateService(awsOptions.CreateServiceClient<IAmazonTranslate>());
			var comprehendService = new ComprehendService(awsOptions.CreateServiceClient<IAmazonComprehend>());
			var comprehendMedicalService = new ComprehendService(awsOptions.CreateServiceClient<IAmazonComprehendMedical>());
			var elasticSearchService = new ElasticSearchService(ElasticSearchEndpoint, ElasticSearchDomainName);

			switch(firstArg) {
				case "--detect-text-local":
					new DetectTextHandler(textractTextService).Handle(LocalEmploymentFile);
					break;
				case "--detect-text-s3":
					new DetectTextS3Handler(textractTextService).Handle(BucketName, S3File);
					break;
				case "--pdf-text":
					new PdfTextHandler(textractTextService).Handle(BucketName, PdfFile);
					break;
				case "--reading-order":
					new ReadingOrderHandler(textractTextService).Handle(BucketName, TwoColumnImage);
					break;
				case "--translate":
					new TranslateHandler(textractTextService, translateService).Handle(BucketName, S3File);
					break;
				case "--search":
					new SearchHandler(textractTextService, elasticSearchService).Handle(BucketName, S3File);
					break;
				case "--forms":
					new FormsHandler(textractAnalysisService).Handle(BucketName, FormFile);
					break;
				case "--forms-redaction":
					new FormsRedactionHandler(textractAnalysisService).Handle(BucketName, FormFile, LocalFolder, LocalEmploymentFile);
					break;
				case "--tables":
					new TablesHandler(textractAnalysisService).Handle(BucketName, FormFile);
					break;
				case "--tables-expense":
					new TablesExpenseHandler(textractAnalysisService).Handle(BucketName, ExpenseFile);
					break;
				case "--nlp-comprehend":
					new NlpComprehendHandler(textractTextService, comprehendService).Handle(LocalSimpleFile);
					break;
				case "--nlp-medical":
					new NlpComprehendMedicalHandler(textractTextService, comprehendMedicalService).Handle(LocalMedicalFile);
					break;
				default:
					Console.WriteLine(HelpText);
					break;
			}
		}

		const string HelpText = @"
            Usage: dotnet run [--switch]
            To run this console app, use the following valid switches one at a time:
				--detect-text-local
				--detect-text-s3
				--pdf-text
				--forms
				--forms-redaction
				--tables
				--tables-expense
				--reading-order
				--nlp-comprehend
				--nlp-medical
				--translate
				--search
                e.g. dotnet run --detect-text-s3
            ";
	}
}