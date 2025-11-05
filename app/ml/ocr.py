from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import base64
import os

def image_to_data_url(image_path: str) -> str:
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    mime = "image/jpeg" if image_path.lower().endswith(".jpg") else "image/png"
    return f"data:{mime};base64,{b64}"

llm = ChatOpenAI(
    model="qwen-vl-plus",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("DASHSCOPE_BASE_URL"),
    temperature=0.0,
    max_tokens=2048
)

def extract_text_from_image(image_path: str) -> str:
    data_url = image_to_data_url(image_path)
    messages = [
        HumanMessage(
            content=[
                {"type": "image_url", "image_url": {"url": data_url}},
                {"type": "text", "text": "你是一位文字提取专家，请将图片中的文字提取成LaTex格式的文本，请只输出提取后的文本，不要改动文本内容，也不要输出任何其余内容"}
            ]
        )
    ]
    response = llm.invoke(messages)
    return response.content