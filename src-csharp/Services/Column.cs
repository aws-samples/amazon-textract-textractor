namespace Dotnet_Core.Services {
	internal class Column {
		public float Left { get; set; }
		public float Right { get; set; }

		public override string ToString() {
			return string.Format("Left: {0}, Right :{1}", this.Left, this.Right);
		}
	}
}