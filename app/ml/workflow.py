import json
from typing import TypedDict, Optional
from app.ml.correction import (
    grading_logic,
    _extract_first_json_object,
    _escape_newlines_inside_json_strings,
)
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END
from app.schemas.correction import CorrectionResponse

import os
from dotenv import load_dotenv

load_dotenv()

class State(TypedDict):
    question: str
    correct_answer: str
    student_answer: str
    grader_output: dict  # 初次批改结果
    reviewer_output: dict  # 审计结果
    final_output: dict  # 最终输出结果
    is_uncertain: bool  # 是否需要前端显示警告标志

def _parse_to_dict_only(raw: str) -> dict:
    json_blob = _extract_first_json_object(raw) or raw
    json_blob = json_blob.replace('\\', '\\\\')
    json_blob = json_blob.replace('\\\\"', '\\"').replace('\\\\n', '\\n')
    json_blob = _escape_newlines_inside_json_strings(json_blob)

    return json.loads(json_blob)

llm = ChatOpenAI(
    model="qwen3-max",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("DASHSCOPE_BASE_URL"),
    temperature=0.0
)

def grader_node(state: State):
    res = grading_logic(state['question'], state['student_answer'], state['correct_answer'])
    return {"grader_output": res.dict(), "is_uncertain": False}


def reviewer_node(state: State):
    reviewer_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a strict Senior High School Math Audit Specialist responsible for verifying the reliability of AI-generated grading results. 

    Your strictly defined protocols:

    1. CORE LIMITATIONS (MUST OBEY):
       - You are NOT allowed to re-grade the student's answer.
       - You are NOT allowed to provide correct solutions or new conclusions.
       - Your SOLE task is to determine if the current grading result is logically sound and consistent.

    2. AUDIT CHECKLIST:
       - Consistency: Does 'is_correct' align perfectly with the 'analysis'?
       - Error Mapping: If 'is_correct' is false, does the 'error_type' match the description in 'analysis'?
       - Accuracy: Does the 'analysis' accurately reflect the student's actual response? Does it identify a real error?
       - Logic: Does the 'analysis' itself contain any mathematical errors or logical contradictions?

    3. JUDGMENT CRITERIA:
       - Mark as FAIL (is_valid: false) if:
         * There is a contradiction between the judgment and the analysis.
         * The identified error location does not exist in the student's work.
         * The analysis contains objective mathematical or conceptual flaws.
       - Mark as PASS (is_valid: true) if:
         * The grading is logically consistent and factually grounded, even if the analysis is brief.

    4. OUTPUT FORMAT:
       - You must output ONLY a valid JSON object. No markdown, no explanation.
       - If valid: {{"is_valid": true}}
       - If invalid: {{"is_valid": false, "issue_description": "Clear description of the logical flaw in the grading (in English)."}}
    
    5. TOLERANCE: 
       - If the student answer is identical to the correct answer, prioritize passing (is_valid: true) unless there is a severe mathematical fallacy.
    
    Maintain an objective and professional tone. Ensure all backslashes in LaTeX are properly escaped."""),
        ("human", """Question: {question}

    Student's Answer: {student_answer}

    AI Grading Result to Audit:
    {grader_output}""")
    ])

    chain = reviewer_prompt | llm | StrOutputParser()
    raw_res = chain.invoke({
        "question": state['question'],
        "student_answer": state['student_answer'],
        "grader_output": json.dumps(state['grader_output'])
    })

    try:
        parsed_dict = _parse_to_dict_only(raw_res)
        return {"reviewer_output": parsed_dict}
    except Exception as e:
        print(f"Reviewer parsing logic error: {e}")
        return {"reviewer_output": {"is_valid": True}}


def regrader_node(state: State):
    regrade_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert High School Mathematics Teacher performing a secondary review of a student's answer.

    Strict Rules for Re-grading:

    1. INDEPENDENT JUDGMENT:
       - You must evaluate the student's answer independently.
       - You may receive 'Reviewer Feedback' regarding a previous grading attempt. Treat this feedback as a reference ONLY; it may be inaccurate. 
       - Only mark the answer as incorrect if YOU identify a definitive mathematical error.

    2. EVALUATION LOGIC:
       - If the student's answer is mathematically equivalent to the correct answer (regardless of the expression format), mark it as CORRECT.
       - Otherwise, mark it as INCORRECT.

    3. ERROR TAXONOMY (Strictly choose one if incorrect):
       - "knowledge": Conceptual misunderstanding.
       - "calculation": Arithmetic or algebraic computation error.
       - "misreading": Failure to interpret the question constraints correctly.
       - "logic": Flawed derivation or structural reasoning.
       - "method": Inappropriate or invalid mathematical approach.

    4. OUTPUT FORMAT:
       - Output ONLY a single JSON object. No Markdown, no preamble.
       - If correct: {{"is_correct": true, "message": "The answer is mathematically correct."}}
       - If incorrect: {{"is_correct": false, "error_type": "...", "analysis": "..."}}

    5. ANALYSIS REQUIREMENTS:
       - Must be written in English.
       - Specifically pinpoint the exact step or concept where the error occurred.
       - Tone: Instructional, encouraging, and clear.
       - DO NOT mention terms like "audit", "review", or "secondary grading" in the analysis.

    Ensure the JSON is valid and all LaTeX expressions are correctly escaped."""),
        ("human", """Question: {question}

    Correct Answer: {correct_answer}

    Student's Answer: {student_answer}

    Reference Audit Feedback (for context):
    {reviewer_feedback}""")
    ])

    chain = regrade_prompt | llm | StrOutputParser()
    raw_res = chain.invoke({
        "question": state['question'],
        "correct_answer": state['correct_answer'],
        "student_answer": state['student_answer'],
        "reviewer_feedback": state['reviewer_output'].get('issue_description', "")
    })

    data = _parse_to_dict_only(raw_res)
    return {"final_output": data, "is_uncertain": True}

def finalize_node(state: State):
    return {"final_output": state['grader_output'], "is_uncertain": False}


workflow = StateGraph(State)

workflow.add_node("grader", grader_node)
workflow.add_node("reviewer", reviewer_node)
workflow.add_node("regrader", regrader_node)
workflow.add_node("finalize", finalize_node)

workflow.set_entry_point("grader")
workflow.add_edge("grader", "reviewer")


# 决策路由
def should_regrade(state: State):
    if state["reviewer_output"].get("is_valid") is True:
        return "pass"
    return "fail"


workflow.add_conditional_edges(
    "reviewer",
    should_regrade,
    {
        "pass": "finalize",
        "fail": "regrader"
    }
)

workflow.add_edge("regrader", END)
workflow.add_edge("finalize", END)

smart_grader_app = workflow.compile()

def smart_grading_entry(question: str, student_answer: str, correct_answer: str) -> CorrectionResponse:
    initial_state = {
        "question": question,
        "student_answer": student_answer,
        "correct_answer": correct_answer,
        "grader_output": {},
        "reviewer_output": {},
        "final_output": {},
        "is_uncertain": False
    }
    final_state = smart_grader_app.invoke(initial_state)
    result_data = final_state.get("final_output", {})

    try:
        return CorrectionResponse(**result_data)
    except Exception:
        return CorrectionResponse(**final_state['grader_output'])