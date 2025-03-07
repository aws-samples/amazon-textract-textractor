import logging
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

logger = logging.getLogger(__name__)

def converter(response):
    blocks_to_delete = []
    page_blocks = []
    try:
        for i, block in enumerate(response["Blocks"]):
            if block.get("BlockType") == "PAGE":
                page_blocks.append(block)
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
        
        blocks_to_delete_id_set = set([b["Id"] for _, b in blocks_to_delete])
        for page_block in page_blocks:
            for relationship in page_block.get("Relationships", []):
                if relationship["Type"] == "CHILD":
                    relationship["Ids"] = [
                        id
                        for id in relationship["Ids"]
                        if id not in blocks_to_delete_id_set
                    ]
                    break
            
        for i, block in blocks_to_delete[::-1]:
            del response["Blocks"][i]
    except Exception as ex:
        logger.warning(f"Failed to convert the response for backward compatibility. {str(ex)}")
    
    return response
