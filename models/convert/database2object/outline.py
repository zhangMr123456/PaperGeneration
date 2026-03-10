from typing import List

from core.graph.utils import flatten_outlines_auto_parent_id
from models.agent.textbook import Outline as OutlineBO, Outlines as OutlinesBO
from models.db.mysql_model import Outline as OutlineDO


def outline_do2bo(outline_bo: OutlineDO) -> OutlineBO:
    outline_do = OutlineBO(
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


def insert_tree(tree: List[OutlineBO], outline: OutlineBO):
    if not outline.parent_id:
        tree.append(outline)
        return
    for index in range(1, len(tree) + 1):
        _outline = tree[-index]
        if _outline.id == outline.parent_id:
            _outline.children.append(outline)
            break
        elif _outline.children:
            insert_tree(_outline.children, outline)


def convert(outline: OutlineDO | List[OutlineDO]) -> OutlineBO | List[OutlineBO]:
    if isinstance(outline, OutlineDO):
        return outline_do2bo(outline)
    elif isinstance(outline, list):
        # 首先根据开始行进行排序
        _outlines = [outline_do2bo(item) for item in outline.copy()]
        _outlines.sort(key=lambda item: item.begin_line_index)
        outline_tree = []
        # 开始构建树结构
        while _outlines:
            _outline = _outlines.pop(0)
            insert_tree(outline_tree, _outline)
        return outline_tree
    else:
        raise TypeError("不支持的格式")


