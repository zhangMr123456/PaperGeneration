from itertools import chain
from langgraph.graph import StateGraph, START, END

from core.chain.politics import knowledge_points_chain
from core.chain.textbook import textbook_info_chain, textbook_outline_chain
from core.custom_enum.textbook_enum import ProcessStageEnum, OutlineStageEnum
from core.graph.subjects import subject_graph_map
from core.graph.utils import flatten_outlines
from core.utils.graph import update_stage
from db.query.mysql_query import db_query
from models.agent.textbook import DocumentContext, DocumentMetadata, Outlines as OutlinesBO, Outline as OutlineBO, \
    SubjectContext
from models.convert.database2object.outline import convert as outline_do2bo
from models.convert.object2database.outline import convert as outline_bo2do
from models.db.mysql_model import Outline as OutlineDO


@update_stage(ProcessStageEnum.PARSE_OUTLINE)
def parse_outline(state: DocumentContext):
    """解析大纲"""
    file_path = state.md_path
    print("parse_outline file_path: ", file_path)

    exists = db_query.exists(OutlineDO, document_context_id=state.id)
    if exists:
        outline_dos = db_query.get_all(OutlineDO, document_context_id=state.id)
        outlines = outline_do2bo(outline_dos)
        state.outlines = outlines
        return state

    # 获取大纲
    with open(file_path, "r", encoding="utf-8") as file:
        markdown_content = file.read()
        _outline: OutlinesBO = textbook_outline_chain.invoke({"input_text": markdown_content[:3000]})
        outlines = _outline.outlines
    # 获取标题所在行
    level_one_titles, max_line_index = [], 0
    for i, line_content in enumerate(markdown_content.split("\n")):
        if line_content.lstrip(" ").startswith("#"):
            level_one_titles.append((i + 1, line_content.replace(" ", "")))
        max_line_index = i + 1

    # 生成大纲开始行和结束行和文档关联
    for outline in flatten_outlines(outlines):
        outline.document_context_id = state.id
        for i, (line_index, level_one_title) in enumerate(level_one_titles):
            title = outline.title.replace(" ", "")
            if title not in level_one_title:
                continue
            outline.begin_line_index = line_index
            level_one_titles = level_one_titles[i + 1:]
            break
        else:
            outline.begin_line_index = -1
    for outline, outline1 in zip(
            chain([None], flatten_outlines(outlines)),
            chain(flatten_outlines(outlines), [None])):
        if outline is None:
            continue
        if outline1 is None:
            end_line_index = max_line_index
        else:
            end_line_index = outline1.begin_line_index
        outline.end_line_index = end_line_index

    # 写入数据库
    outline_dos = outline_bo2do(outlines)
    db_query.add_all(outline_dos)

    state.outlines = outlines
    return state


@update_stage(ProcessStageEnum.PARSE_TEXTBOOK_INFO)
def parse_textbook(state: DocumentContext):
    """解析课本信息"""
    file_path = state.md_path
    print("parse_textbook file_path: ", file_path)
    if state.subject and state.grade:
        return state

    # 获取大纲
    with open(file_path, "r", encoding="utf-8") as file:
        markdown_content = file.read()
        document_data_meta: DocumentMetadata = textbook_info_chain.invoke({"input_text": markdown_content[:3000]})
        state.subject = document_data_meta.subject
        state.grade = document_data_meta.grade
        state.doc_type = document_data_meta.doc_type
        state.confidence = document_data_meta.confidence
        state.evidence = document_data_meta.evidence
    return state


@update_stage(ProcessStageEnum.PARSE_KNOWLEDGE)
def parse_subsection(state: DocumentContext):
    """解析段落"""
    outlines = state.outlines
    if not outlines:
        return state

    file_path = state.md_path
    print("parse_subsection file_path: ", file_path)

    with open(file_path, "r", encoding="utf-8") as file:
        markdown_content = file.read()

    markdown_content_lines = markdown_content.split("\n")

    for (outline, depth, max_depth, titles) in flatten_outlines(outlines, mark_depth=True):
        if not max_depth:
            continue
        # 已经处理的不重复处理
        if outline.stage == OutlineStageEnum.DONE:
            continue

        begin_line_index = outline.begin_line_index
        end_line_index = outline.end_line_index
        section_text = "\n".join(markdown_content_lines[begin_line_index - 1: end_line_index - 1])
        section_title = "-".join(titles)
        subject_context = SubjectContext(
            document=state,
            outline=outline,
            section_title=section_title,
            section_text=section_text,
            knowledge=None
        )
        try:
            subject_graph = subject_graph_map.get(state.subject)
            subject_graph.invoke(subject_context)
        except:
            raise
            import traceback
            traceback.print_exc()
            traceback.print_stack()
            outline.stage = OutlineStageEnum.ERROR
        else:
            outline.stage = OutlineStageEnum.NOT_DONE
        db_query.update(outline)


graph = StateGraph(DocumentContext)
graph.add_node("parse_textbook", parse_textbook)
graph.add_node("parse_outline", parse_outline)
graph.add_node("parse_subsection", parse_subsection)

graph.add_edge(START, "parse_textbook")
graph.add_edge("parse_textbook", "parse_outline")
graph.add_edge("parse_outline", "parse_subsection")
graph.add_edge("parse_subsection", END)
graph = graph.compile()


if __name__ == '__main__':
    test_state = DocumentContext(
        md_path=r"D:\Project\Python\TestPaperGeneration\TestPaperGeneration\extension\MonkeyOCR\output\普通高中教科书 思想政治 必修2 经济与社会_1756191823687\普通高中教科书 思想政治 必修2 经济与社会_1756191823687.md"
    )
    graph.invoke(test_state)
