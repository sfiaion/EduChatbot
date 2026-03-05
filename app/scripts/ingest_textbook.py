# app/scripts/ingest_textbook.py
import os
import sys
import pathlib
from pdf2image import convert_from_path
from dotenv import load_dotenv, find_dotenv, dotenv_values
from sqlalchemy.orm import Session
import json

# Add project root to sys.path
PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.db.session import SessionLocal
from app.models.rag import RagPassage
from app.ml.ocr import _get_llm, image_to_data_url
from langchain_core.messages import HumanMessage

# Configuration
# 教材目录：c:\Users\86138\Desktop\笔记集\项目\education_AI\book
TEXTBOOK_DIR = r"C:\Users\86138\Desktop\笔记集\项目\education_AI\EduChatbot\book"
TEMP_IMG_DIR = os.path.join(PROJECT_ROOT, "temp_images")
os.makedirs(TEMP_IMG_DIR, exist_ok=True)

def ocr_and_chunk_page(image_path, page_no):
    """使用 Qwen-VL 对整页进行 OCR 并按语义切分"""
    llm = _get_llm()
    data_url = image_to_data_url(image_path)
    
    prompt = """你是一位教材数字化专家。请识别这张图片中的教材内容，并按语义单元（如：定义、定理、例题、例题解析、练习说明）进行切分。
要求：
1. 使用 LaTeX 格式保留所有数学公式。
2. 输出符合以下格式的 JSON 数组：
   [
     {
       "content": "该单元的完整文本内容，包含 LaTeX 公式",
       "category": "definition/theorem/example/explanation",
       "metadata": {"chapter": "第X章", "section": "第X节", "title": "知识点标题"}
     }
   ]
3. 只输出 JSON 数组本身，不要包含任何 Markdown 代码块或解释性文字。"""
    
    messages = [
        HumanMessage(content=[
            {"type": "image_url", "image_url": {"url": data_url}},
            {"type": "text", "text": prompt}
        ])
    ]
    
    try:
        response = llm.invoke(messages)
        content = str(response.content or "")
        
        # 清理可能存在的 Markdown 代码块标记
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        # 寻找数组的开始和结束
        start = content.find("[")
        end = content.rfind("]") + 1
        if start != -1 and end != -1:
            json_str = content[start:end]
            chunks = json.loads(json_str)
            return chunks
        else:
            print(f"Warning: No JSON array found in response for page {page_no}")
            return []
    except Exception as e:
        print(f"Error processing page {page_no}: {e}")
        return []

def ingest_textbooks(limit_pages=None):
    """
    解析教材并存入数据库
    limit_pages: 每个 PDF 处理的页数限制, 设为 None 表示处理所有页面
    """
    db: Session = SessionLocal()
    try:
        # 加载环境变量
        dotenv_path = PROJECT_ROOT / '.env'
        load_dotenv(dotenv_path=dotenv_path, encoding='utf-8')
        poppler_path = os.getenv("Poppler_PATH")

        if not os.path.exists(TEXTBOOK_DIR):
            print(f"Error: Textbook directory {TEXTBOOK_DIR} does not exist.")
            return

        for pdf_file in os.listdir(TEXTBOOK_DIR):
            if not pdf_file.endswith(".pdf"):
                continue
            
            pdf_path = os.path.join(TEXTBOOK_DIR, pdf_file)
            print(f"🚀 开始处理教材: {pdf_file}...")
            
            try:
                # 将 PDF 转为图像 (需要安装 poppler)
                if not poppler_path or not os.path.exists(poppler_path):
                    print(f"Error: Poppler_PATH environment variable not set or path does not exist.")
                    continue
                images = convert_from_path(pdf_path, first_page=1, last_page=limit_pages, poppler_path=poppler_path)
                
                for i, image in enumerate(images):
                    page_no = i + 1
                    img_name = f"{pdf_file}_p{page_no}.jpg"
                    img_path = os.path.join(TEMP_IMG_DIR, img_name)
                    image.save(img_path, "JPEG")
                    
                    print(f"  📄 正在处理第 {page_no} 页...")
                    chunks = ocr_and_chunk_page(img_path, page_no)
                    
                    if not chunks:
                        print(f"  ⚠️ 第 {page_no} 页未提取到有效内容。")
                        continue

                    for chunk in chunks:
                        passage = RagPassage(
                            content=chunk.get("content"),
                            source=pdf_file,
                            page_no=page_no,
                            category=chunk.get("category"),
                            metadata_json=chunk.get("metadata")
                        )
                        db.add(passage)
                    
                    db.commit()
                    print(f"  ✅ 第 {page_no} 页处理完成，提取了 {len(chunks)} 个片段。")
                    
                    # 清理临时图片
                    if os.path.exists(img_path):
                        os.remove(img_path)
                        
            except Exception as e:
                print(f"❌ 处理 PDF {pdf_file} 时出错: {e}")
                continue
        
        print("\n✨ 所有教材解析任务已完成！")
    finally:
        db.close()
        # 清理临时目录
        if os.path.exists(TEMP_IMG_DIR) and not os.listdir(TEMP_IMG_DIR):
            os.rmdir(TEMP_IMG_DIR)

if __name__ == "__main__":
    target_pages = 200
    print(f"设定处理页数上限为: {target_pages}")
    ingest_textbooks(limit_pages=target_pages)
