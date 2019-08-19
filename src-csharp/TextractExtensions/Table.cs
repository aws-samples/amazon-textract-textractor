using System;
using System.Collections.Generic;

namespace Amazon.Textract.Model {
	public class Table {
		public Table(Block block, List<Block> blocks) {
			this.Block = block;
			this.Confidence = block.Confidence;
			this.Geometry = block.Geometry;
			this.Id = block.Id;
			this.Rows = new List<Row>();
			var ri = 1;
			var row = new Row();

			var relationships = block.Relationships;
			if(relationships != null && relationships.Count > 0) {
				relationships.ForEach(r => {
					if(r.Type == "CHILD") {
						r.Ids.ForEach(id => {
							var cell = new Cell(blocks.Find(b => b.Id == id), blocks);
							if(cell.RowIndex > ri) {
								this.Rows.Add(row);
								row = new Row();
								ri = cell.RowIndex;
							}
							row.Cells.Add(cell);
						});
						if(row != null && row.Cells.Count > 0)
							this.Rows.Add(row);
					}
				});
			}
		}
		public List<Row> Rows { get; set; }
		public Block Block { get; set; }
		public float Confidence { get; set; }
		public Geometry Geometry { get; set; }
		public string Id { get; set; }

		public override string ToString() {
			var result = new List<string>();
			result.Add(string.Format("Table{0}===={0}", Environment.NewLine));
			this.Rows.ForEach(r => {
				result.Add(string.Format("Row{0}===={0}{1}{0}", Environment.NewLine, r));
			});
			return string.Join("", result);
		}
	}
}