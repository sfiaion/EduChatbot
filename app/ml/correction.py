from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from app.schemas.correction import CorrectionRequest, CorrectionResponse, ErrorType
import os
from typing import List, Optional, Tuple
from app.models.question import Question, KnowledgeNode

def grading_logic(
    question: str,
    student_answer: str,
    correct_answer: str
) -> CorrectionResponse:
    llm = ChatOpenAI(
        model="qwen3-max",
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url=os.getenv("DASHSCOPE_BASE_URL"),
        temperature=0.0,
        max_tokens=2048
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一位高中数学老师，请严格按以下规则批改学生答案：
    1. 判断逻辑：
        如果学生答案与标准答案在数学上等价（允许不同表达形式），视为正确。
        否则视为错误。
    2. 输出格式（必须严格遵守，只输出 JSON，不要任何其他文字）：
        若正确，输出：{{"is_correct": true, "message": "答案正确"}}
        若错误，输出：{{"is_correct": false, "error_type": "...", "analysis": "..."}}
    3. 错误类型（error_type）必须从以下5个值中选择其一：
        "knowledge"（知识点错误）
        "calculation"（计算错误）
        "misreading"（审题错误）
        "logic"（逻辑错误）
        "method"（方法错误）
    4. analysis 要求：
        用中文书写；
        具体指出错误出现在哪一步或哪个概念；
        语气友善，具有教学指导意义。
    请只输出一个 JSON 对象，不要 Markdown、不要解释、不要额外字段。请确保输出是合法 JSON，如果使用反斜杠，请正确转义。"""),
        ("human", "题目：{question}\n\n标准答案：{correct_answer}\n\n学生答案：{student_answer}")
    ])
    parser = JsonOutputParser(pydantic_object=CorrectionResponse)
    chain = prompt | llm | parser
    try:
        result = chain.invoke({
            "question": question,
            "student_answer": student_answer,
            "correct_answer": correct_answer
        })
        return result
    except Exception as e:
        print(f"解析失败: {e}")
        return CorrectionResponse(
            is_correct=False,
            error_type=ErrorType.KNOWLEDGE,
            analysis="批改结果解析失败，请重试。"
        )

def _escape_curly_braces(text: str) -> str:
    return text.replace("{", "{{").replace("}", "}}")

def identify_knowledge_from_candidates(
    question: str,
    student_answer: str,
    correct_answer: str,
    candidates: List[KnowledgeNode]
) -> int:
    if not candidates:
        print("无候选知识点")
        return -1
    candidate_text = "\n".join([
        f"{i}. {_escape_curly_braces(node.name)} : {_escape_curly_braces(node.content)}"
        for i, node in enumerate(candidates, 1)
    ])

    llm = ChatOpenAI(
        model="qwen3-max",
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url=os.getenv("DASHSCOPE_BASE_URL"),
        temperature=0.0,
        max_tokens=100
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一位资深高中数学教师。学生在解答一道数学题时出现了知识点性错误。
        请根据题目、标准答案和学生答案，从以下候选知识点中选择**最可能未掌握**的一项。
        只输出序号（如 "3"），不要任何解释、标点或额外文字。"""),
        ("human", f"""题目：{question}
        标准答案：{correct_answer}
        学生答案：{student_answer}
        候选知识点：
        {candidate_text}""")
    ])
    chain = prompt | llm | StrOutputParser()
    try:
        output = chain.invoke({})
        idx = int(output.strip()) - 1  # 转为 0-based 索引
        if 0 <= idx < len(candidates):
            print(f"二次判断 → 知识点 ID: {candidates[idx].id} | {candidates[idx].name}")
            return candidates[idx].id
        else:
            print("二次判断：序号超出范围")
            return -1
    except Exception as e:
        print(f"二次判断失败: {e}")
        return -1