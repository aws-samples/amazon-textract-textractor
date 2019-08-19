/*
class SelectionElement:
    def __init__(self, block, blockMap):
        self._confidence = block['Confidence']
        self._geometry = Geometry(block['Geometry'])
        self._id = block['Id']
        self._selectionStatus = block['SelectionStatus']

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
    def selectionStatus(self):
        return self._selectionStatus
 */

using System.Collections.Generic;

namespace Amazon.Textract.Model {
	public class SelectionElement {
		public SelectionElement(Block block, List<Block> blocks) {
			this.Confidence = block.Confidence;
			this.Geometry = block.Geometry;
			this.Id = block.Id;
			this.SelectionStatus = block.SelectionStatus;
		}
		public float Confidence { get; set; }
		public Geometry Geometry { get; set; }
		public string Id { get; set; }
		public string SelectionStatus { get; set; }

	}
}