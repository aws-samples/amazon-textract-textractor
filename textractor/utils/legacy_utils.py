from textractor.data.constants import (
    LAYOUT_FIGURE,
    LAYOUT_LIST,
    LAYOUT_TABLE,
    LAYOUT_KEY_VALUE,
    LAYOUT_TEXT,
    LAYOUT_TITLE,
    LAYOUT_HEADER,
    LAYOUT_FOOTER,
    LAYOUT_SECTION_HEADER,
    LAYOUT_PAGE_NUMBER,
)

def converter(response):
    blocks_to_delete = []
    page_block = None
    for i, block in enumerate(response["Blocks"]):
        if block.get("BlockType") == "PAGE":
            page_block = block
        elif block.get("BlockType", "").startswith("LAYOUT_FIGURE_"):
            block["BlockType"] = LAYOUT_TEXT
        elif (
            block.get("BlockType", "").startswith("LAYOUT_") and
            block.get("BlockType") not in [
                LAYOUT_TEXT,
                LAYOUT_TITLE,
                LAYOUT_HEADER,
                LAYOUT_FOOTER,
                LAYOUT_SECTION_HEADER,
                LAYOUT_PAGE_NUMBER,
                LAYOUT_LIST,
                LAYOUT_FIGURE,
                LAYOUT_TABLE,
                LAYOUT_KEY_VALUE,
            ]
        ):
            block["BlockType"] = LAYOUT_FIGURE
        elif block.get("BlockType") == LAYOUT_FIGURE and "CONTAINER" in block.get("EntityTypes", []):
            blocks_to_delete.append((i, block))
    
    page_relationships = []
    for relationship in page_block["Relationships"]:
        if relationship["Type"] == "CHILD":
            page_relationships = relationship["Ids"]
            break
        
    for i, block in blocks_to_delete[::-1]:
        del response["Blocks"][i]
        page_relationships.remove(block["Id"])
    
    return response
