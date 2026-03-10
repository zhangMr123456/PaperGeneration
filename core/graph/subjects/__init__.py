from typing import Dict

from langgraph.graph.state import CompiledStateGraph

from core.custom_enum.textbook_enum import SubjectEnum
from core.graph.subjects.politics import graph as politics_graph

subject_graph_map: Dict[SubjectEnum, CompiledStateGraph] = {
    SubjectEnum.POLITICS: politics_graph
}