/*
class Word:
    def __init__(self, block, blockMap):
        self._block = block
        self._confidence = block['Confidence']
        self._geometry = Geometry(block['Geometry'])
        self._id = block['Id']
        self._text = ""
        if(block['Text']):
            self._text = block['Text']

    def __str__(self):
        return self._text

    @property
    def confidence(self):
        return self._confidence

    @property
    def geometry(self):
        return self._geometry

    @property
    def id(self):
        return self._id

    @property
    def text(self):
        return self._text

    @property
    def block(self):
        return self._block
 */

using System.Collections.Generic;

namespace Amazon.Textract.Model {
	public class Word {
		public Word(Block block, List<Block> blocks) {
			this.Block = block;
			this.Confidence = block.Confidence;
			this.Geometry = block.Geometry;
			this.Id = block.Id;
			this.Text = block == null ? string.Empty : block.Text;
		}

		public Block Block { get; set; }
		public float Confidence { get; set; }
		public Geometry Geometry { get; set; }
		public string Id { get; set; }
		public string Text { get; set; }

		public override string ToString() {
			return Text;
		}
	}
}