# app/ml/correction.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from app.schemas.correction import CorrectionRequest, CorrectionResponse, ErrorType
import os
import json
from typing import List, Optional, Tuple
from app.models.question import Question, KnowledgeNode

def _extract_first_json_object(text: str) -> str | None:
    if not text:
        return None
    start = text.find("{")
    if start < 0:
        return None
    depth = 0
    in_str = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
            continue
        else:
            if ch == '"':
                in_str = True
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
    return None

def _escape_newlines_inside_json_strings(s: str) -> str:
    if not s:
        return s
    out: list[str] = []
    in_str = False
    escape = False
    for ch in s:
        if in_str:
            if escape:
                out.append(ch)
                escape = False
                continue
            if ch == "\\":
                out.append(ch)
                escape = True
                continue
            if ch == '"':
                out.append(ch)
                in_str = False
                continue
            if ch == "\n":
                out.append("\\n")
                continue
            if ch == "\r":
                continue
            out.append(ch)
            continue
        else:
            if ch == '"':
                out.append(ch)
                in_str = True
                continue
            out.append(ch)
    return "".join(out)

def _parse_correction_response(raw: str) -> CorrectionResponse:
    json_blob = _extract_first_json_object(raw) or raw
    json_blob = _escape_newlines_inside_json_strings(json_blob)
    data = json.loads(json_blob)
    if isinstance(data, dict):
        return CorrectionResponse(**data)
    raise ValueError("Invalid correction response type")

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
        ("system", """You are a high school math teacher. Grade the student's answer strictly as follows:
    1. Decision rule:
        If the student's answer is mathematically equivalent to the correct answer (even if expressed differently), it is correct.
        Otherwise, it is incorrect.
    2. Output format (STRICT: output ONLY a single JSON object, no extra text):
        If correct: {{"is_correct": true, "message": "Correct"}}
        If incorrect: {{"is_correct": false, "error_type": "...", "analysis": "..."}}
    3. error_type MUST be one of:
        "knowledge", "calculation", "misreading", "logic", "method"
    4. analysis requirements:
        Write in English;
        Point out exactly which step or concept is wrong;
        Be friendly and instructional.
    Output ONLY a valid JSON object. No Markdown, no explanation outside JSON. Ensure proper escaping if backslashes are used."""),
        ("human", "Question: {question}\n\nCorrect Answer: {correct_answer}\n\nStudent Answer: {student_answer}")
    ])
    chain = prompt | llm | StrOutputParser()
    try:
        raw = chain.invoke({
            "question": question,
            "student_answer": student_answer,
            "correct_answer": correct_answer
        })
        return _parse_correction_response(raw)
    except Exception as e:
        print(f"Parse failed: {e}")
        return CorrectionResponse(
            is_correct=False,
            error_type=ErrorType.KNOWLEDGE,
            analysis="Failed to parse grading result. Please retry."
        )

def _escape_curly_braces(text: str) -> str:
    return text.replace("{", "{{").replace("}", "}}")

import re

def identify_knowledge_from_candidates(
    question: str,
    student_answer: str,
    correct_answer: str,
    candidates: List[KnowledgeNode]
) -> int:
    if not candidates:
        return -1
    
    # Limit candidates to prevent token overflow
    candidates_subset = candidates[:20]
    
    candidate_text = "\n".join([
        f"{i}. {_escape_curly_braces(node.name)} : {_escape_curly_braces(node.content)}"
        for i, node in enumerate(candidates_subset, 1)
    ])

    llm = ChatOpenAI(
        model="qwen3-max",
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url=os.getenv("DASHSCOPE_BASE_URL"),
        temperature=0.0,
        max_tokens=100
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a senior high school math teacher.
        Identify the single most likely missing knowledge point based on the student's error.
        
        CRITICAL INSTRUCTION:
        Output ONLY a JSON object with a single key "index".
        Example: {{"index": 3}}
        Do NOT output any text, explanation, or reasoning.
        """),
        ("human", """Question: {question}
        Correct Answer: {correct_answer}
        Student Answer: {student_answer}
        Candidate Knowledge Points:
        {candidate_text}""")
    ])
    chain = prompt | llm | JsonOutputParser()
    try:
        output = chain.invoke({
            "question": question,
            "correct_answer": correct_answer,
            "student_answer": student_answer,
            "candidate_text": candidate_text
        })
        
        # Output should be a dict like {"index": 3}
        if isinstance(output, dict) and "index" in output:
            idx = int(output["index"]) - 1
            if 0 <= idx < len(candidates_subset):
                print(f"Secondary Check -> ID: {candidates_subset[idx].id} | {candidates_subset[idx].name}")
                return candidates_subset[idx].id
        
        print(f"Secondary Check Failed: Invalid output format {output}")
        return candidates_subset[0].id # Fallback
    except Exception as e:
        print(f"Secondary Check Error: {e}")
        return candidates_subset[0].id if candidates_subset else -1

def generate_hint(
    question: str,
    student_answer: str,
    correct_answer: str,
    attempt_count: int = 1
) -> str:
    def _truncate_words(s: str, limit: int = 80) -> str:
        try:
            words = s.strip().split()
            if len(words) <= limit:
                return s.strip()
            return " ".join(words[:limit]).strip()
        except Exception:
            return s

    llm = ChatOpenAI(
        model="qwen3-max",
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url=os.getenv("DASHSCOPE_BASE_URL"),
        temperature=0.7,
        max_tokens=500
    )

    hint_strategy = ""
    if attempt_count == 1:
        hint_strategy = """
        - Level 1 Hint: Focus on the INITIAL STEP or CONCEPT.
        - Identify the specific discrepancy between the student's starting point and the correct approach.
        - Be encouraging but point them in the right direction.
        - Example: "You're close, but check how you handled the logarithm coefficient."
        """
    elif attempt_count == 2:
        hint_strategy = """
        - Level 2 Hint: Focus on the CALCULATION or LOGICAL GAP.
        - Point out exactly where the error likely occurred (without giving the answer).
        - Example: "Remember that 2lg2 becomes lg(2^2). Did you subtract correctly?"
        """
    else:
        hint_strategy = """
        - Level 3 Hint (Final Attempt): Explain the FULL STRATEGY.
        - Outline the steps: Step 1 -> Step 2 -> Step 3.
        - This is the "Giveaway" strategy but still requires them to do the final math.
        """

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful and Socratic teacher.
        The student has answered incorrectly. Current Attempt: {attempt_count}/3.
        
        Your Goal: Provide a specific, targeted hint in English based on the Student's actual error, in <= 80 words.
        
        Strategy for this attempt:
        {hint_strategy}
        
        Instructions:
        1. Compare the Student Answer "{student_answer}" with the Correct Answer "{correct_answer}".
        2. Identify the specific mistake (e.g., wrong formula, arithmetic error, conceptual misunderstanding).
        3. Write a hint that addresses THIS specific mistake.
        4. Keep it concise (no more than 80 words).
        5. Avoid headings, lists, code blocks, or markdown formatting.
        6. If math is necessary, include at most ONE short LaTeX expression (like \\log_2 9), otherwise use plain text.
        7. Do NOT reveal the final answer directly.
        8. Output MUST be in English.
        """),
        ("human", """Question: {question}
        Correct Answer: {correct_answer}
        Student Answer: {student_answer}
        """)
    ])
    chain = prompt | llm | StrOutputParser()
    try:
        text = chain.invoke({
            "question": question, 
            "correct_answer": correct_answer, 
            "student_answer": student_answer,
            "attempt_count": attempt_count,
            "hint_strategy": hint_strategy
        })
        return _truncate_words(text, 80)
    except Exception as e:
        print(f"Hint generation error: {e}")
        return "It looks like a small issue. Check the question and your calculation again!"
