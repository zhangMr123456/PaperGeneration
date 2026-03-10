from typing import List

from core.graph.utils import flatten_outlines_auto_parent_id
from models.agent.textbook import Outline as OutlineBO, Outlines as OutlinesBO
from models.db.mysql_model import Outline as OutlineDO


def outline_bo2do(outline_bo: OutlineBO) -> OutlineDO:
    outline_do = OutlineDO(
        id=outline_bo.id,
        document_context_id=outline_bo.document_context_id,
        title=outline_bo.title,
        page_index=outline_bo.page_index,
        begin_line_index=outline_bo.begin_line_index,
        end_line_index=outline_bo.end_line_index,
        parent_id=outline_bo.parent_id,
        extra=outline_bo.extra,
        stage=outline_bo.stage
    )
    return outline_do


def convert(outline: OutlineBO | List[OutlineBO]) -> OutlineDO | List[OutlineDO]:
    if isinstance(outline, OutlineBO):
        return outline_bo2do(outline)
    elif isinstance(outline, List):
        outline_dos, outlines = [], outline
        for outline in flatten_outlines_auto_parent_id(outlines):
            outline_dos.append(
                outline_bo2do(outline)
            )
        return outline_dos
    else:
        raise TypeError("不支持的格式")
