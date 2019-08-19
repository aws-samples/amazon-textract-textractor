namespace Amazon.Textract.Model {
	public class NewBoundingBox : BoundingBox {
		public NewBoundingBox(float width, float height, float left, float top) : base() {
			this.Width = width;
			this.Height = height;
			this.Left = left;
			this.Top = top;
		}

		public override string ToString() {
			return string.Format("width: {0}, height: {1}, left: {2}, top: {3}", Width, Height, Left, Top);
		}
	}
}