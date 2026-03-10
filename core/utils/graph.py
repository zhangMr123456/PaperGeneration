from core.custom_enum.textbook_enum import ProcessStageEnum
from db.query.mysql_query import db_query
from models.agent.textbook import DocumentContext as DocumentContextBO
from models.convert.object2database.document import convert as document_bo2do


def update_stage(stage: ProcessStageEnum):
    def __exe__(func):
        def __inner__(state: DocumentContextBO, *args, **kwargs):
            state.stage = stage
            print(state, f"改变为: {stage}")
            db_query.update(document_bo2do(state))
            return func(state, *args, **kwargs)
        return __inner__
    return __exe__