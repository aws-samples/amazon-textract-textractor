/*

class FieldKey:
    def __init__(self, block, children, blockMap):
        self._block = block
        self._confidence = block['Confidence']
        self._geometry = Geometry(block['Geometry'])
        self._id = block['Id']
        self._text = ""
        self._content = []

        t = []

        for eid in children:
            wb = blockMap[eid]
            if(wb['BlockType'] == "WORD"):
                w = Word(wb, blockMap)
                self._content.append(w)
                t.append(w.text)

        if(t):
            self._text = ' '.join(t)

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
    def content(self):
        return self._content

    @property
    def text(self):
        return self._text

    @property
    def block(self):
        return self._block

 */

using System.Collections.Generic;

namespace Amazon.Textract.Model {
	public class FieldKey {
		public FieldKey(Block block, List<string> children, List<Block> blocks) {
			this.Block = block;
			this.Confidence = block.Confidence;
			this.Geometry = block.Geometry;
			this.Id = block.Id;
			this.Text = string.Empty;
			this.Content = new List<dynamic>();

			var words = new List<string>();

			if(children != null && children.Count > 0) {
				children.ForEach(c => {
					var wordBlock = blocks.Find(b => b.Id == c);
					if(wordBlock.BlockType == "WORD") {
						var w = new Word(wordBlock, blocks);
						this.Content.Add(w);
						words.Add(w.Text);
					}
				});
			}

			if(words.Count > 0) {
				this.Text = string.Join(" ", words);
			}

		}
		public List<dynamic> Content { get; set; }
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