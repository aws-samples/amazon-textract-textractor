using System;
using System.Collections.Generic;

namespace Amazon.Textract.Model {
	public class NewGeometry : Geometry {

		public NewGeometry(Geometry geometry) : base() {
			this.BoundingBox = geometry.BoundingBox;
			this.Polygon = geometry.Polygon;
			var bb = new NewBoundingBox(this.BoundingBox.Width, this.BoundingBox.Height, this.BoundingBox.Left, this.BoundingBox.Top);
			var pgs = new List<Point>();
			Polygon.ForEach(pg => pgs.Add(new Point {
				X = pg.X,
				Y = pg.Y
			}));

			BoundingBox = bb;
			Polygon = pgs;
		}

		public override string ToString() {
			return string.Format("BoundingBox: {0}{1}", BoundingBox, Environment.NewLine);
		}


	}
}