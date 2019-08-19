using System.Collections.Generic;

namespace Amazon.Textract.Model {
	public class Row {
		public Row() {
			this.Cells = new List<Cell>();
		}
		public List<Cell> Cells { get; set; }

		public override string ToString() {
			var result = new List<string>();
			this.Cells.ForEach(c => {
				result.Add(string.Format("[{0}]", c));
			});
			return string.Join("", result);
		}
	}
}