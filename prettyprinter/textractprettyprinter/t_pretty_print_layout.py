import os
import warnings
import logging
from trp.trp2 import TDocument
from typing import List

logger = logging.getLogger(__name__)

class LinearizeLayout:
    def __init__(self, 
                 textract_json: dict, 
                 table_format: str = "grid", 
                 exclude_figure_text: bool=True,
                 exclude_page_header: bool=False, 
                 exclude_page_footer: bool=False, 
                 exclude_page_number: bool=False,
                 skip_table: bool=False,
                 save_txt_path: str=None, 
                 generate_markdown: bool=False):
        self.j = textract_json
        self.table_format = table_format
        self.exclude_figure_text = exclude_figure_text
        self.exclude_page_header = exclude_page_header
        self.exclude_page_footer = exclude_page_footer
        self.exclude_page_number = exclude_page_number
        self.skip_table = skip_table
        self.save_txt_path = save_txt_path
        self.generate_markdown = generate_markdown
        self.figures = []
        
    def _get_layout_blocks(self) -> tuple:
        """Get all blocks of type 'LAYOUT' and a dictionary of Ids mapped to their corresponding block."""
        layouts = [{"Id": x['Id'], "Page": x.get('Page',1)} for x in self.j['Blocks'] if x['BlockType'].startswith('LAYOUT')]
        id2block = {x['Id']: x for x in self.j['Blocks']}
        self.figures = [{"page": block.get('Page', 1), "geometry": block['Geometry']['BoundingBox']} \
                        for block in self.j['Blocks'] \
                        if block['BlockType'] == 'LAYOUT_FIGURE']

        """Avoid duplicating list contents: exclude LAYOUT* elements that are children of LAYOUT_LIST elements."""
        list_layout_child_ids = set()
        for layout in layouts:
            layout_block = id2block[layout["Id"]]
            if layout_block["BlockType"] != "LAYOUT_LIST":
                continue
            for relationship in [
                r for r in layout_block.get("Relationships", []) if r["Type"] == "CHILD"
            ]:
                for rel_id in relationship["Ids"]:
                    if id2block[rel_id]["BlockType"].startswith('LAYOUT'):
                        list_layout_child_ids.add(rel_id)
        layouts = [
            layout for layout in layouts if layout["Id"] not in list_layout_child_ids
        ]

        if not layouts:
            logger.warning("No LAYOUT information found in Textract response. \
                           Please use LAYOUT feature for AnalyzeDocument API call \
                           for optimum output")
        return layouts, id2block

    def _geometry_match(self, geom1, geom2, tolerance=0.1):
        """Check if two geometries match within a given tolerance."""
        for key in ['Width', 'Height', 'Left', 'Top']:
            if abs(geom1[key] - geom2[key]) > tolerance:
                return False
        return True

    def _is_inside(self, inner_geom, outer_geom):
        """Check if inner geometry is fully contained within the outer geometry."""
        inner_left, inner_top, inner_right, inner_bottom = (
            inner_geom['Left'], 
            inner_geom['Top'], 
            inner_geom['Left'] + inner_geom['Width'], 
            inner_geom['Top'] + inner_geom['Height']
        )
        
        outer_left, outer_top, outer_right, outer_bottom = (
            outer_geom['Left'], 
            outer_geom['Top'], 
            outer_geom['Left'] + outer_geom['Width'], 
            outer_geom['Top'] + outer_geom['Height']
        )
        
        return (inner_left >= outer_left and inner_right <= outer_right and 
                inner_top >= outer_top and inner_bottom <= outer_bottom)
    
    def _validate_block_skip(self, blockType: str) -> bool:
        if self.exclude_page_header and blockType == "LAYOUT_HEADER":
            return True
        elif self.exclude_page_footer and blockType == "LAYOUT_FOOTER":
            return True
        elif self.exclude_page_number and blockType == "LAYOUT_PAGE_NUMBER":
            return True
        else:
            return False
    
    def _dfs(self, root, id2block):
        texts = []
        stack = [(root, 0)]

        while stack:
            block_id, depth = stack.pop()
            block = id2block[block_id]
            
            if self._validate_block_skip(block["BlockType"]):
                continue
            
            # Handle LAYOUT_TABLE type
            if not self.skip_table and block["BlockType"] == "LAYOUT_TABLE":
                table_data = []
                # Find the matching TABLE block for the LAYOUT_TABLE
                table_block = None
                for potential_table in [b for b in self.j['Blocks'] if b['BlockType'] == 'TABLE' and b.get('Page',1) == block.get('Page', 1)]:
                    if self._geometry_match(block['Geometry']['BoundingBox'], potential_table['Geometry']['BoundingBox']):
                        table_block = potential_table
                        break

                if table_block and "Relationships" in table_block:
                    table_content = {}
                    headers = {}
                    max_row = 0
                    max_col = 0
                    for cell_rel in table_block["Relationships"]:
                        if cell_rel['Type'] == "CHILD":
                            for cell_id in cell_rel['Ids']:
                                cell_block = id2block[cell_id]
                                if "Relationships" in cell_block:
                                    cell_text = " ".join([id2block[line_id]['Text'] for line_id in cell_block["Relationships"][0]['Ids'] if 'Text' in id2block[line_id]])
                                    row_idx = cell_block['RowIndex']
                                    col_idx = cell_block['ColumnIndex']
                                    max_row = max(max_row, row_idx)
                                    max_col = max(max_col, col_idx)
                                    for r in range(cell_block.get('RowSpan', 1)):
                                        for c in range(cell_block.get('ColumnSpan', 1)):
                                            if "EntityTypes" in cell_block and "COLUMN_HEADER" in cell_block["EntityTypes"]:
                                                headers[col_idx + c] = cell_text
                                            else:
                                                table_content[(row_idx + r, col_idx + c)] = cell_text
                    
                    table_data = []
                    start_row = 2 if headers else 1
                    for r in range(start_row, max_row + 1):
                        row_data = []
                        for c in range(1, max_col + 1):
                            row_data.append(table_content.get((r, c), ""))
                        table_data.append(row_data)

                    header_list = [headers.get(c, "") for c in range(1, max_col + 1)]
                
                    try:
                        from tabulate import tabulate
                    except ImportError:
                        raise ModuleNotFoundError(
                            "Could not import tabulate python package. "
                            "Please install it with `pip install tabulate`."
                        )
                        
                    tab_fmt = "pipe" if self.generate_markdown else self.table_format
                    '''If Markdown is enabled then default to pipe for tables'''
                    
                    table_text = tabulate(table_data, headers=header_list, tablefmt=tab_fmt)
                    yield table_text
                    continue
                else:
                    logger.warning("LAYOUT_TABLE detected but TABLES feature was not provided in API call. \
                                  Inlcuding TABLES feature may improve the layout output")
                    
            if block["BlockType"] == "LINE" and "Text" in block:
                if self.exclude_figure_text and self.figures:
                    if any(self._is_inside(block['Geometry']['BoundingBox'], figure_geom["geometry"]) \
                           for figure_geom in self.figures if figure_geom["page"] == block.get("Page",1)):
                        continue
                yield block['Text']
            elif block["BlockType"] in ["LAYOUT_TITLE", "LAYOUT_SECTION_HEADER"] and "Relationships" in block:
                # Get the associated LINE text for the layout
                line_texts = [id2block[line_id]['Text'] for line_id in block["Relationships"][0]['Ids']]
                combined_text = ' '.join(line_texts)

                # Prefix with appropriate markdown
                if self.generate_markdown:
                    if block["BlockType"] == "LAYOUT_TITLE":
                        combined_text = f"# {combined_text}"
                    elif block["BlockType"] == "LAYOUT_SECTION_HEADER":
                        combined_text = f"## {combined_text}"
                yield combined_text
                
            if block["BlockType"].startswith('LAYOUT') and block["BlockType"] not in ["LAYOUT_TITLE", "LAYOUT_SECTION_HEADER"]:
                if "Relationships" in block:
                    relationships = block["Relationships"]
                    children = [(x, depth + 1) for x in relationships[0]['Ids']]            
                    stack.extend(reversed(children))
    
    def _save_to_s3(self, page_texts: dict) -> None:
        try:
            import boto3
            import re
            s3 = boto3.client('s3')            
            match = re.match(r's3://([^/]+)(?:/(.*))?', self.save_txt_path)
            bucket = match.group(1)
            prefix = match.group(2) if match.group(2) else ""
            
            for page_number, content in page_texts.items():
                file_name = f"{page_number}.txt"
                s3_key = os.path.join(prefix, file_name)
                logger.debug(f"Writing linearized text for page {page_number} to bucket {bucket} file {s3_key}")
                s3.put_object(Body=content, 
                              Bucket=bucket, 
                              Key=s3_key)
        except ImportError:
            logger.error("Could not import boto3 python package. \
                          Please install it with `pip install boto3`.")
            raise ModuleNotFoundError(
                "Could not import boto3 python package. "
                "Please install it with `pip install boto3`."
            )
        except Exception as e:
            logger.error(e)
            raise e
    
    def _save_to_files(self, page_texts: dict) -> None:
        path = self.save_txt_path.rstrip(os.sep)
        if path.startswith('s3://'):
            self._save_to_s3(page_texts=page_texts)
        else:
            for page_number, content in page_texts.items():            
                file_path = os.path.join(path, f"{page_number}.txt")
                logger.debug(f"Writing linearized text for page {page_number} to file {file_path}")
                with open(file_path, "w") as f:
                    f.write(content)
                
    def get_text(self) -> dict:
        """Retrieve the text content in specified format. Default is CSV. Options: "csv", "markdown"."""
        # texts = []
        page_texts = {}
        layouts, id2block = self._get_layout_blocks()
        for layout in layouts:
            root = layout['Id']
            page_number = layout.get('Page', 1)
            if page_number not in page_texts:
                page_texts[page_number] = ""
            page_texts[page_number] += '\n'.join(self._dfs(root, id2block))+ "\n\n"
        if self.save_txt_path:
            self._save_to_files(page_texts)
        return page_texts

def string_counter():
    # Dictionary to keep track of the occurrences of each string
    occurrences = {}
    def counter(string):
        if string in occurrences:
            occurrences[string] += 1
        else:
            occurrences[string] = 1
        return occurrences[string]

    return counter

def get_layout_csv_from_trp2(trp2_doc: TDocument) -> List[List[List[str]]]:
    """
    Generate the layout.csv from the Amazon Textract Web Console download
    This does generate for each page a list of the entries:

    'Page number','Layout','Text','Reading Order','Confidence score'

    Page number     : Starting at 1, incrementing for each page
    Layout          : The BlockType + a number indicating the sequence for 
                      this BlockType starting at 1 and for LAYOUT_LIST elements 
                      the string:  "- part of LAYOUT_LIST (index)" is added
    Text            : The underlying text (except LAYOUT_LIST and LAYOUT_FIGURE )
    Reading Order   : Increasing int for each LAYOUT element starting with 0
    Confidence score: Confidence in this being a LAYOUT element
    """
    result_value:List[List[List[str]]] = list()

    counter_instance = string_counter()
    for page_number, page in enumerate(trp2_doc.pages):
        page_result:List[List[str]] = list()
        processed_ids = []
        relationships: t2.TRelationship = page.get_relationships_for_type()
        blocks = [trp2_doc.get_block_by_id(id) for id in relationships.ids if relationships.ids]
        layout_blocks = [
            block for block in blocks if block.block_type in [
                "LAYOUT_TITLE", "LAYOUT_HEADER", "LAYOUT_FOOTER", "LAYOUT_SECTION_HEADER", "LAYOUT_PAGE_NUMBER",
                "LAYOUT_LIST", "LAYOUT_FIGURE", "LAYOUT_TABLE", "LAYOUT_KEY_VALUE", "LAYOUT_TEXT"
            ]
        ]
        for idx, layout_block in enumerate(layout_blocks):
            # for lists the output is special, because the LAYOUT_TEXTs do have a reference to the LAYOUT_LIST in the text
            # so we grab the list and process all children
            # probably could make this "easier" by keeping track of the len of CHILD relationships in LAYOUT_LIST
            # but wanted to see if I can prepare the lists in lists, which may happen one point in the future...
            if layout_block.block_type == "LAYOUT_LIST":
                # first print out the LAYOUT_LIST
                block_type_count = counter_instance(layout_block.block_type)
                page_result.append([str(page_number + 1), layout_block.block_type + " " + str(block_type_count), "", str(idx),
                                              layout_block.block_type, str(layout_block.confidence)])

                # print(page_number + 1, layout_block.block_type + " " + str(block_type_count), "", idx, layout_block.block_type)
                list_context_name = layout_block.block_type + " " + str(block_type_count)
                # now get the relationships
                list_block_rel = layout_block.get_relationships_for_type()
                if list_block_rel:
                    # get the text relationships
                    list_child_blocks = [trp2_doc.get_block_by_id(id) for id in list_block_rel.ids]
                    for child_idx, list_child_block in enumerate(list_child_blocks):
                        block_type_count = counter_instance(list_child_block.block_type)
                        child_block_relation_text = list_child_block.block_type + " " + str(
                            block_type_count) + " - part of " + list_context_name
                        # get the text, meaning get all the child relationships
                        layout_child_block_rel = list_child_block.get_relationships_for_type()
                        layout_child_line_blocks = [
                            trp2_doc.get_block_by_id(id) for id in layout_child_block_rel.ids
                            if layout_child_block_rel.ids
                        ]
                        # get the text, but not for figures
                        layout_text = trp2_doc.get_text_for_tblocks(
                            layout_child_line_blocks) if list_child_block.block_type != "LAYOUT_FIGURE" else ""

                        page_result.append([str(page_number + 1), child_block_relation_text, layout_text, str(idx + child_idx + 1), list_child_block.block_type, str(list_child_block.confidence)])
                        # print(page_number + 1, child_block_relation_text, layout_text, idx + child_idx + 1,
                        #         list_child_block.block_type)
                        processed_ids.append(list_child_block.id)
            elif layout_block.id not in processed_ids:
                layout_block_rel = layout_block.get_relationships_for_type()

                # Bug fix - #284
                if layout_block_rel is None:
                    logger.info (f'Block {layout_block} has no relationships')
                    continue

                layout_blocks = [
                    trp2_doc.get_block_by_id(id) for id in layout_block_rel.ids if layout_block_rel.ids
                ]
                # get the text, but not for figures
                layout_text = trp2_doc.get_text_for_tblocks(
                    layout_blocks) if layout_block.block_type != "LAYOUT_FIGURE" else ""
                block_type_count = counter_instance(layout_block.block_type)
                page_result.append([str(page_number + 1), layout_block.block_type + " " + str(block_type_count), layout_text, str(idx),
                                              layout_block.block_type, str(layout_block.confidence)])
                # print(page_number + 1, layout_block.block_type + " " + str(block_type_count), layout_text, idx, layout_block.block_type)

        result_value.append(page_result)
    return result_value
