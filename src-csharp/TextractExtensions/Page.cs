using System.Dynamic;
using System;
using System.Collections.Generic;

namespace Amazon.Textract.Model {

	public class Page {
		public Page(List<Block> blocks, List<Block> blockMap) {
			this.Blocks = blocks;
			this.Text = string.Empty;
			this.Lines = new List<Line>();
			this.Form = new Form();
			this.Tables = new List<Table>();
			this.Content = new List<dynamic>();

			blocks.ForEach(b => {
				if(b.BlockType == "PAGE") {
					this.Geometry = new NewGeometry(b.Geometry);
					this.Id = b.Id;
				} else if(b.BlockType == "LINE") {
					var l = new Line(b, blockMap);
					this.Lines.Add(l);
					this.Content.Add(l);
					this.Text = this.Text + l.Text + Environment.NewLine;
				} else if(b.BlockType == "TABLE") {
					var t = new Table(b, blockMap);
					this.Tables.Add(t);
					this.Content.Add(t);
				} else if(b.BlockType == "KEY_VALUE_SET") {
					if(b.EntityTypes.Contains("KEY")) {
						var f = new Field(b, blockMap);
						if(f.Key != null) {
							this.Form.AddField(f);
							this.Content.Add(f);
						}
					}
				}
			});

		}

		public List<IndexedText> GetLinesInReadingOrder() {
			var lines = new List<IndexedText>();
			var columns = new List<Column>();
			this.Lines.ForEach(line => {
				var columnFound = false;
				for(var index = 0; index < columns.Count; index++) {
					var column = columns[index];
					var bb = line.Geometry.BoundingBox;
					var bbLeft = bb.Left;
					var bbRight = bb.Left + bb.Width;
					var bbCentre = bb.Left + (bb.Width / 2);
					var columnCentre = column.Left + (column.Right / 2);

					if((bbCentre > column.Left && bbCentre < column.Right) || (columnCentre > bbLeft && columnCentre < bbRight)) {
						lines.Add(new IndexedText { ColumnIndex = index, Text = line.Text });
						columnFound = true;
						break;
					}
				}
				if(!columnFound) {
					var bb = line.Geometry.BoundingBox;
					columns.Add(new Column { Left = bb.Left, Right = bb.Left + bb.Width });
					lines.Add(new IndexedText { ColumnIndex = columns.Count - 1, Text = line.Text });
				}
			});
			lines.FindAll(line => line.ColumnIndex == 0).ForEach(line => Console.WriteLine(line));
			return lines;
		}

		public string GetTextInReadingOrder() {
			var lines = this.GetLinesInReadingOrder();
			var text = string.Empty;
			lines.ForEach(line => {
				text = text + line.Text + "\n";
			});
			return text;
		}


		public List<Block> Blocks { get; set; }
		public string Text { get; set; }
		public List<Line> Lines { get; set; }
		public Form Form { get; set; }
		public List<Table> Tables { get; set; }
		public List<dynamic> Content { get; set; }
		public Geometry Geometry { get; set; }
		public string Id { get; set; }

		public override string ToString() {
			var result = new List<string>();
			result.Add(string.Format("Page{0}===={0}", Environment.NewLine));
			this.Content.ForEach(c => {
				result.Add(string.Format("{1}{0}", Environment.NewLine, c));
			});
			return string.Join("", result);
		}

		public class Column {
			public float Left { get; set; }
			public float Right { get; set; }

			public override string ToString() {
				return string.Format("Left: {0}, Right :{1}", this.Left, this.Right);
			}
		}

		public class IndexedText {
			public int ColumnIndex { get; set; }
			public string Text { get; set; }

			public override string ToString() {
				return string.Format("[{0}] {1}", this.ColumnIndex, this.Text);
			}
		}
	}
}
