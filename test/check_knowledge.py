# test/check_knowledge.py
import os
import sys
from pathlib import Path

# 将项目根目录（edu_chatbot_backend）加入 Python 模块搜索路径
PROJECT_ROOT = Path(__file__).parent.parent  # 上两级：test/ → 项目根
sys.path.insert(0, str(PROJECT_ROOT))

# 现在可以使用绝对导入
from app.db.session import engine
from sqlalchemy import text

# 确保 test 目录存在（其实当前就在 test 下，但保险起见）
os.makedirs('test', exist_ok=True)

with engine.connect() as conn:
    result = conn.execute(
        text("SELECT content FROM knowledge_nodes WHERE name = '幂函数值域'")
    ).fetchone()

if result:
    content = result[0]
    print("✅ 实际 content（直接打印）：")
    with open('test/debug_latex.txt', 'w', encoding='utf-8') as f:
        f.write(content)

    # 检查是否真的有 \\alpha
    if "\\alpha" in content and "\\\\alpha" not in content:
        print("\n🟢 正常：只有一个反斜杠，KaTeX 能识别")
    elif "\\\\alpha" in content:
        print("\n🔴 危险：有两个反斜杠，需要清洗")
else:
    print("未找到")