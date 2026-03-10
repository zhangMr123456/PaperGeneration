from typing import List, Tuple

from models.agent.textbook import Outline as OutlineBO


def flatten_outlines(outlines, mark_depth=False):
    """扁平化大纲结构

    Args:
        outlines: 大纲列表
        mark_depth: 是否标记深度和叶节点状态
    """
    def _flatten(_outlines, depth=0, titles=[]):
        """内部递归函数，depth参数外部不可访问"""
        for outline in _outlines:
            children = outline.children
            if mark_depth:
                yield outline, depth, not bool(children), titles + [outline.title]
            else:
                yield outline
            yield from _flatten(children, depth + 1, titles + [outline.title])

    return _flatten(outlines)


def flatten_outlines_auto_parent_id(outlines, mark_depth=False):
    """扁平化大纲结构

    Args:
        outlines: 大纲列表
        mark_depth: 是否标记深度和叶节点状态
    """
    def _flatten(_outlines, depth=0, titles=[], parent_id=None):
        """内部递归函数，depth参数外部不可访问"""
        for outline in _outlines:
            children = outline.children
            outline.parent_id = parent_id
            if mark_depth:
                yield outline, depth, not bool(children), titles + [outline.title]
            else:
                yield outline
            yield from _flatten(children, depth + 1, titles + [outline.title], outline.id)

    return _flatten(outlines)
