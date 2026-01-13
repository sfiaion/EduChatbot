# app/services/chat.py

import os
from fastapi import HTTPException
from dashscope import Generation
from ..crud.chat_session import get_session_history, update_session_history
from sqlalchemy.orm import Session


def get_api_key():
    key = os.getenv("DASHSCOPE_API_KEY")
    if not key:
        raise HTTPException(status_code=500, detail="DASHSCOPE_API_KEY not set in .env")
    return key

def normalize_markdown_latex(text: str) -> str:
    try:
        import re
        s = text or ""
        # 将 $$ 换行块转为 \[ ... \]（避免 markdown 段落拆分影响）
        s = re.sub(r"(^|\r?\n)\s*\$\$\s*(?:\r?\n)([\s\S]*?)(?:\r?\n)\s*\$\$(?=\r?\n|$)", r"\1\\[\2\\]", s)
        # 将 [ ... ] 中的对齐/分段环境转换为 \[ ... \]
        s = re.sub(
            r"\[\s*([\s\S]*?\\begin\{(?:aligned|cases)\}[\s\S]*?\\end\{(?:aligned|cases)\}[\s\S]*?)\s*\]",
            r"\\[\1\\]", s)
        # 行尾单反斜杠换行修正为 \\（避免对代码块的影响，仅限普通文本）
        s = re.sub(r"(?<!\\)\\\s*$", r"\\\\", s, flags=re.MULTILINE)
        # 函数名与变量连写：\sin alpha -> \sin\alpha、\cos x -> \cos x（保留合法写法）
        s = re.sub(r"\\(sin|cos|tan|cot|sec|csc)\s+([a-zA-Z])", r"\\\1\\\2", s)
        # 向量参数补齐：\vec a -> \vec{a}
        s = re.sub(r"\\vec\s+([a-zA-Z])", r"\\vec{\1}", s)
        # log 下标空格：\log _a -> \log_a
        s = re.sub(r"\\log\s+_([a-zA-Z])", r"\\log_\1", s)
        # 常见误写控制序列：\x、\y 等移除反斜杠
        s = re.sub(r"\\([xy])\b", r"\1", s)
        return s
    except Exception:
        return text

async def stream_chat(messages: list):
    """Stream DashScope qwen3-max"""
    api_key = get_api_key()

    try:
        guard = {
            "role": "system",
            "content": (
                "You are a Learning Assistant. Only handle study-related questions (subject knowledge, problem solving, solution steps, study methods, exam strategies, homework help, knowledge graph explanations, etc.). "
                "Politely refuse unrelated topics with: \"I focus on study-related questions. Please keep the conversation on learning topics.\" "
                "\nOutput in English with Markdown; use LaTeX for math."
                "\nDelimiters: inline $...$ or \\(...\\), block \\[...\\]; if using $$, keep the expression within a single paragraph (no standalone $$ lines)."
                "\nFormatting: for multi-line math, use \\begin{aligned} ... \\end{aligned}, lines separated by \\\\ and aligned with &."
                "\nFunctions and symbols: write \\sin\\alpha, \\cos\\beta, \\tan\\theta, \\ln x, \\log_a M, \\frac{a}{b}."
                "\nVectors: write \\vec{v}, magnitude |\\vec{v}|."
                "\nDo not output single backslash line breaks; do not separate function names from variables (avoid \"\\sin alpha\")."
                "\nStructure the answer with clear steps, key formulas, and conclusions."
            )
        }
        final_messages = [guard] + messages
        responses = Generation.call(
            api_key=api_key,
            model="qwen3-max",
            messages=final_messages,
            stream=True,
            incremental_output=True,
            result_format="message"
        )

        for response in responses:
            if response.status_code != 200:
                raise HTTPException(
                    status_code=500,
                    detail=f"DashScope error: {response.code} - {response.message}"
                )

            choices = response.output.get("choices", [])
            if choices and "message" in choices[0]:
                content = choices[0]["message"].get("content", "")
                if content:
                    yield content
            elif "text" in response.output:
                text = response.output.get("text", "")
                if text:
                    yield text

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stream failed: {str(e)}")


def save_message_to_history(db: Session, session_id: str, user_msg: str, ai_reply: str):
    history = get_session_history(db, session_id)
    history.extend([
        {"role": "user", "content": user_msg},
        {"role": "assistant", "content": normalize_markdown_latex(ai_reply)}
    ])
    update_session_history(db, session_id, history)
