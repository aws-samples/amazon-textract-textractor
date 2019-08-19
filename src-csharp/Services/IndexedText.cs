namespace Dotnet_Core.Services {
	internal class IndexedText {
		public int ColumnIndex { get; set; }
		public string Text { get; set; }

		public override string ToString() {
			return string.Format("[{0}] {1}", this.ColumnIndex, this.Text);
		}
	}
}