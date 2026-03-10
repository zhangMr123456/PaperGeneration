from models.agent.textbook import DocumentContext as DocumentContextBO
from models.db.mysql_model import DocumentContext as DocumentContextDO


def convert(document: DocumentContextBO) -> DocumentContextDO:
    document_do = DocumentContextDO(
        id=document.id,
        file_name=document.file_name,
        file_md5=document.file_md5,
        pdf_path=document.pdf_path,
        md_path=document.md_path,
        stage=document.stage,
        subject=document.subject,
        grade=document.grade,
        doc_type=document.doc_type,
        confidence=document.confidence,
        evidence=document.evidence,
        user_id=document.user_id,
    )
    return document_do
