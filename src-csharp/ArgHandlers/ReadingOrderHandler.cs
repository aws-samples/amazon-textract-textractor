using System;
using System.Collections.Generic;
using Dotnet_Core.Services;

namespace Dotnet_Core.ArgHandlers {
	internal class ReadingOrderHandler {
		private readonly TextractTextDetectionService textractTextService;

		public ReadingOrderHandler(TextractTextDetectionService textractTextService) {
			this.textractTextService = textractTextService;
		}

		internal void Handle(string bucketName, string twoColumnImage) {
			var task = textractTextService.StartDocumentTextDetection(bucketName, twoColumnImage);
			var jobId = task.Result;
			textractTextService.WaitForJobCompletion(jobId);
			var jobResults = textractTextService.GetJobResults(jobId);
			var lines = new List<IndexedText>();
			var columns = new List<Column>();
			jobResults.ForEach(job => {
				job.Blocks.ForEach(block => {
					if(block.BlockType == "LINE") {
						var columnFound = false;
						for(var index = 0; index < columns.Count; index++) {
							var column = columns[index];
							var bb = block.Geometry.BoundingBox;
							var bbLeft = bb.Left;
							var bbRight = bb.Left + bb.Width;
							var bbCentre = bb.Left + (bb.Width / 2);
							var columnCentre = column.Left + (column.Right / 2);

							if((bbCentre > column.Left && bbCentre < column.Right) || (columnCentre > bbLeft && columnCentre < bbRight)) {
								lines.Add(new IndexedText { ColumnIndex = index, Text = block.Text });
								columnFound = true;
								break;
							}
						}
						if(!columnFound) {
							var bb = block.Geometry.BoundingBox;
							columns.Add(new Column { Left = bb.Left, Right = bb.Left + bb.Width });
							lines.Add(new IndexedText { ColumnIndex = columns.Count - 1, Text = block.Text });
						}
					}
				});
				lines.FindAll(line => line.ColumnIndex == 0).ForEach(line => Console.WriteLine(line));
			});
		}
	}
}