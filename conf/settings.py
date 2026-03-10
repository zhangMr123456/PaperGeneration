import os.path

# neo4j 配置
NEO4J_USER_DATABASE = {
    "uri": "neo4j://localhost:7687",
    "username": "",
    "password": ""
}

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MILVUS_URI = ""

DATABASES = {
    "knowledge": {
        "host": "192.168.106.129",
        "user": "",
        "password": "",
        "port": 3306,
        "database": "knowledge"
    }
}

# 百炼Key
BAILIAN_KEY = ""
BAILIAN_API_HOST = "https://dashscope.aliyuncs.com/compatible-mode/v1"
