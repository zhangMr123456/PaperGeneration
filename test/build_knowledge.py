import os.path

from conf.settings import BASE_DIR
from core.custom_enum.textbook_enum import ProcessStageEnum
from core.graph.upload_pdf import graph as upload_graph
from core.utils.cmd import run_python_script
from core.utils.file import get_file_md5
from db.query.mysql_query import db_query
from models.agent.textbook import DocumentContext as DocumentContextBO
from models.db.mysql_model import DocumentContext as DocumentContextDO
from models.convert.object2database.document import convert as document_bo2do
from models.convert.database2object.document import convert as document_do2bo


input_path = r"C:\Users\admin\Desktop\普通高中教科书 思想政治 必修2 经济与社会_1756191823687.pdf"
# 1. 信息入库
print("信息入库")
file_name = os.path.basename(input_path)
file_md5 = get_file_md5(input_path)
document_bo = DocumentContextBO(
    file_name=file_name,
    file_md5=file_md5,
    pdf_path=input_path,
    stage=ProcessStageEnum.INIT,
    done=False
)
document_do = document_bo2do(document_bo)
exists = db_query.exists(DocumentContextDO, file_md5=file_md5)
if exists:
    print(f"数据库存在： {input_path}")
    document_do = db_query.get_one(DocumentContextDO, file_md5=file_md5)
else:
    db_query.add(document_do)
    print(f"插入成功： {input_path}")

# 2. 转为markdown
print("转为markdown")
document_do.stage = ProcessStageEnum.PDF2MARKDOWN
monkeyocr_dir = os.path.join(BASE_DIR, "extension", "MonkeyOCR")
output_dir = os.path.join(monkeyocr_dir, "output")
parse_path = os.path.join(monkeyocr_dir, "parse.py")
dir_name = '.'.join(file_name.split(".")[:-1])
output_path = os.path.join(output_dir, dir_name)
if os.path.isdir(output_path):
    print(f"exists output markdown: {output_path}, continue")
else:
    run_python_script(parse_path, args=[input_path])
# markdown信息入库
print("markdown信息入库")
md_path = os.path.join(output_path, f"{dir_name}.md")
document_do.md_path = md_path
print(md_path)
db_query.update(document_do)

# 3. 调用graph
print("调用graph")
upload_graph.invoke(document_do2bo(document_do))



