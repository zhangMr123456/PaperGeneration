from langchain_openai import ChatOpenAI

from conf.settings import BAILIAN_KEY, BAILIAN_API_HOST
from core.custom_enum.llm_enum import QwenModel

llm = ChatOpenAI(
    # 如果没有配置环境变量，请用阿里云百炼API Key替换：api_key="sk-xxx"
    model=QwenModel.QWEN3_MAX_260123,
    api_key=BAILIAN_KEY,
    base_url=BAILIAN_API_HOST,
    extra_body={"enable_thinking": False}
)

if __name__ == '__main__':
    messages = [{"role": "user", "content": "你是谁"}]
    completion = llm.chat.completions.create(
        model=QwenModel.QWEN3_MAX_260123,  # 您可以按需更换为其它深度思考模型
        messages=messages,
        extra_body={"enable_thinking": False},
        stream=True
    )
    is_answering = False  # 是否进入回复阶段
    print("\n" + "=" * 20 + "思考过程" + "=" * 20)
    for chunk in completion:
        delta = chunk.choices[0].delta
        if hasattr(delta, "reasoning_content") and delta.reasoning_content is not None:
            if not is_answering:
                print(delta.reasoning_content, end="", flush=True)
        if hasattr(delta, "content") and delta.content:
            if not is_answering:
                print("\n" + "=" * 20 + "完整回复" + "=" * 20)
                is_answering = True
            print(delta.content, end="", flush=True)
