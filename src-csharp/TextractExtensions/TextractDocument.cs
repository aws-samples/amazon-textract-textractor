using System.Collections.Generic;

namespace Amazon.Textract.Model {
	public class TextractDocument {
		private List<Block> blockMap = new List<Block>();
		List<List<Block>> documentPages = new List<List<Block>>();

		public TextractDocument(GetDocumentAnalysisResponse response) {
			this.Pages = new List<Page>();
			this.ResponsePages = new List<GetDocumentAnalysisResponse>();
			this.ResponsePages.Add(response);

			this.ParseDocumentPagesAndBlockMap();
			this.Parse();
		}

		private void ParseDocumentPagesAndBlockMap() {
			List<Block> documentPage = null;
			this.ResponsePages.ForEach(page => {
				page.Blocks.ForEach(block => {
					this.blockMap.Add(block);

					if(block.BlockType == "PAGE") {
						if(documentPage != null) {
							this.documentPages.Add(documentPage);
						}
						documentPage = new List<Block>();
						documentPage.Add(block);
					} else {
						documentPage.Add(block);
					}
				});
			});

			if(documentPage != null) {
				this.documentPages.Add(documentPage);
			}

		}

		private void Parse() {
			this.documentPages.ForEach(documentPage => {
				var page = new Page(documentPage, this.blockMap);
				this.Pages.Add(page);
			});
		}

		public Block GetBlockById(string blockId) {
			return this.blockMap.Find(x => x.Id == blockId);
		}

		public List<GetDocumentAnalysisResponse> ResponsePages { get; set; }
		public List<Page> Pages { get; set; }
		public List<List<Block>> PageBlocks {
			get {
				return this.documentPages;
			}
		}
	}
}
