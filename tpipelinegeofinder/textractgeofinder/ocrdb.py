from __future__ import annotations
from textractgeofinder.tword import TWord
import sqlite3
from typing import Iterable, Any, List, Optional
import trp.trp2 as t2
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class AreaSelection:
    top_left: t2.TPoint
    lower_right: t2.TPoint
    page_number: int    # = field(default=1)

    @property
    def area(self) -> float:
        return abs(self.lower_right.x - self.top_left.x) * abs(self.lower_right.y - self.top_left.y)

    def __eq__(self, other: AreaSelection):
        return self.top_left == other.top_left and self.lower_right == other.lower_right

    def __ne__(self, other: AreaSelection):
        return not (self == other)

    def __lt__(self, other: AreaSelection):
        return self.area < other.area

    def __gt__(self, other: AreaSelection):
        return self.area > other.area


class OCRDB():

    __instance = None

    @staticmethod
    def getInstance() -> OCRDB:
        if OCRDB.__instance == None:
            OCRDB()
        if OCRDB.__instance != None:
            return OCRDB.__instance
        raise Exception("could not instantiate OCRDB instance")

    def __init__(self):
        """
        create connection and create DB
        """
        if OCRDB.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            if not hasattr(self, 'conn'):
                self.conn: sqlite3.Connection = sqlite3.connect(':memory:')
                # self.conn.set_trace_callback(print)
                self.__create_database()
                OCRDB.__instance = self

    # Using int to save space (real would be 8 bytes vs 2 bytes for the int value in our case)
    def __create_database(self):
        cursor: sqlite3.Cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE ocrdb
                          (textract_doc_uuid text,
                           page_number int,
                           text_type text,
                           text text,
                           original_text text,
                           confidence real,
                           xmin int,
                           ymin int,
                           xmax int,
                           ymax int,
                           id text NOT NULL PRIMARY KEY,
                           doc_width int,
                           doc_height int,
                           child_relationships text,
                           reference text,
                           FOREIGN KEY(reference) REFERENCES ocrdb(id)
        )''')
        cursor.execute('''CREATE INDEX idx_ocrdb_text_type ON ocrdb (text_type);''')
        cursor.execute('''CREATE INDEX idx_ocrdb_textract_doc_uuid ON ocrdb (textract_doc_uuid);''')
        cursor.execute('''CREATE INDEX idx_ocrdb_page_number ON ocrdb (page_number);''')
        cursor.execute('''CREATE INDEX idx_ocrdb_xmin ON ocrdb (xmin);''')
        cursor.execute('''CREATE INDEX idx_ocrdb_ymin ON ocrdb (ymin);''')
        cursor.execute('''CREATE INDEX idx_ocrdb_xmax ON ocrdb (xmax);''')
        cursor.execute('''CREATE INDEX idx_ocrdb_ymax ON ocrdb (ymax);''')

    def insert(self, textract_doc_uuid, x: TWord):
        # logger.warning(f"insert: {x}")
        cursor: sqlite3.Cursor = self.conn.cursor()
        cursor.execute('INSERT INTO ocrdb VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?)', [
            textract_doc_uuid, x.page_number, x.text_type, x.text, x.original_text, x.confidence, x.xmin, x.ymin,
            x.xmax, x.ymax, x.id, x.doc_width, x.doc_height, x.child_relationships, x.reference
        ])

    def insert_bulk(self, textract_doc_uuid, rows: "list[TWord]"):
        cursor: sqlite3.Cursor = self.conn.cursor()
        cursor.executemany('INSERT INTO ocrdb VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?)', [[
            textract_doc_uuid, x.page_number, x.text_type, x.text, x.original_text, x.confidence, x.xmin, x.ymin,
            x.xmax, x.ymax, x.id, x.doc_width, x.doc_height, x.child_relationships, x.reference
        ] for x in rows])

    # def select_text_type(self, textract_doc_uuid: str,
    #                      text_type: str) -> "list[TWord]":
    #     cursor: sqlite3.Cursor = self.conn.cursor()
    #     result_set = cursor.execute(
    #         'SELECT * FROM ocrdb WHERE textract_doc_uuid=? AND text_type=?',
    #         (textract_doc_uuid, text_type))
    #     return [TWord(ocrdb_row=x) for x in result_set]

    def select_text(self,
                    textract_doc_uuid: str,
                    text: str,
                    area_selection: AreaSelection = None,
                    page_number: int = 1,
                    exclude_ids: List[str] = None) -> "list[TWord]":
        return self.execute(query=" and text=? ",
                            params=[text],
                            textract_doc_uuid=textract_doc_uuid,
                            area_selection=area_selection,
                            page_number=page_number,
                            exclude_ids=exclude_ids)

    def get_id(self, id: str, textract_doc_uuid: str) -> Optional[TWord]:
        cursor: sqlite3.Cursor = self.conn.cursor()
        r = cursor.execute("select * from ocrdb where textract_doc_uuid=? and id=?", (textract_doc_uuid, id))
        rows = [x for x in r]
        if rows:
            if len(rows) > 1:
                logger.warn(f"found more than 1 row with id: {rows}")
            return TWord(ocrdb_row=rows[0])
        else:
            logger.error(f"did not find id: {id} in ocrdb")

    def execute(self,
                query: str,
                params: Iterable[Any],
                textract_doc_uuid,
                area_selection: AreaSelection = None,
                page_number: int = 1,
                exclude_ids: List[str] = None) -> "list[TWord]":

        cursor: sqlite3.Cursor = self.conn.cursor()

        query_composed = "select * from ocrdb where textract_doc_uuid=? and page_number=? "
        params_composed = list()
        params_composed.append(textract_doc_uuid)
        if page_number and area_selection and area_selection.page_number != page_number:
            raise ValueError("page_number and area_selection.page_number are not equal")
        params_composed.append(page_number)
        if area_selection:
            area_xmin = area_selection.top_left.x
            area_ymin = area_selection.top_left.y
            area_xmax = area_selection.lower_right.x
            area_ymax = area_selection.lower_right.y
            query_composed += "  and (ymin + ymax) / 2 > ? \
                        and (ymin + ymax) / 2 < ? \
                        and (xmin + xmax) / 2 > ? \
                        and (xmin + xmax) / 2 < ? \
                        and (page_number) = ?"

            params_composed.extend([area_ymin, area_ymax, area_xmin, area_xmax, area_selection.page_number])
        if exclude_ids:
            query_composed += f" and id not in ({','.join(['?']*len(exclude_ids))}) "
            params_composed.extend(exclude_ids)
        params_composed.extend(params)
        query_composed += query
        logger.debug(f"query: {query_composed}\nparams_initial: {params_composed}")

        return [TWord(ocrdb_row=x) for x in cursor.execute(query_composed, params_composed)]

    def delete(self, textract_doc_uuid):
        cursor: sqlite3.Cursor = self.conn.cursor()
        cursor.execute('''delete from ocrdb where textract_doc_uuid=?''', (textract_doc_uuid, ))
        return cursor.rowcount
