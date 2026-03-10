import os.path

# neo4j 配置
NEO4J_USER_DATABASE = {
    "uri": "neo4j://localhost:7687",
    "username": "neo4j",
    "password": "6c86LxJ7eMdwXnn"
}

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MILVUS_URI = "http://192.168.106.129:19530"

DATABASES = {
    "knowledge": {
        "host": "192.168.106.129",
        "user": "root",
        "password": "YourStrongPassword123",
        "port": 3306,
        "database": "knowledge"
    }
}

# 百炼Key
BAILIAN_KEY = "sk-e5c1e815e62a4f8eb3d6870a0651d7fb"
BAILIAN_API_HOST = "https://dashscope.aliyuncs.com/compatible-mode/v1"
