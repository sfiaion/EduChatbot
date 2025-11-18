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
    model="qwen3-vl-plus",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("DASHSCOPE_BASE_URL"),
    temperature=0.0,
    max_tokens=2048
)

def extract_answer_from_image(image_path: str) -> str:
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

def extract_question_from_image(image_path: str) -> str:
    data_url = image_to_data_url(image_path)
    messages = [
        HumanMessage(
            content=[
                {"type": "image_url", "image_url": {"url": data_url}},
                {"type": "text", "text": r"""
你是一位文字提取专家。请从图片中提取数学题目的题干、选项（如有）、答案和解析。

【严格输出要求】
1. 输出为 txt 格式，不要使用 Markdown，不要使用符号如：*, #, -, ``` 等。
2. 禁止出现**题号**，例如 “1.” “（1）” “1、” 等一切题目前缀编号；禁止出现任何来源/出处，例如年份、课标 I/II、全国卷、地方卷、学校名称等。
3. 每道题输出**恰好两行**：
   第 1 行：题目 + 选项（若有）
   第 2 行：答案（只输出答案本身，不包括“答案”两个字） + 解析
   ——（注意）第1行与第2行之间**绝对不要**使用 "||" 或其它分隔符；也不要在两行之间留空行。
4. 题目中：
   - 题目与选项之间用 "||" 分割
   - 各选项之间也用 "||" 分割
   - 多选题题干最前加 "(多选)"
5. 如果题干、选项、小问、解析中出现原始换行（包括：题干中的段落换行、一个小问到下一个小问的换行、解析内部的换行），必须使用 "||" 替代换行。
   ——规则重点：原文本中只要有换行，就必须输出 "||"，不能漏。
6. 如果原图没有解析，请你自动补全一个合理的解析。
7. 输出中只能包含题目内容，不要包含示例。
8. 所有数学表达式、公式、符号，一律用“$...$”包裹，包括填空题答案中的数字

【格式示例】
示例 1（填空题）：
已知函数 f(x)=ax^3-2x 的图像过点 (-1,4)，则 a=________ 
-2 || 解析：将点代入方程求得。

示例 2（单选题）：
若 f(x)=(x+a)*ln((2x-1)/(2x+1)) 为偶函数，则 a= || A.-1 || B.0 || C.1/2 || D.1
B || 解析：由 f(-x)=f(x) 可得 a=0。

示例 3（多选题）：
(多选) 已知 f(xy)=y^2 f(x)+x^2 f(y)，则 || A.f(0)=0 || B.f(1)=0 || C.f(x) 为偶函数 || D.x=0 为极小值点
ABC || 解析：分别代入 0、1、-1 可得出结论。

示例 4（解答题）：
春运是中国在农历春节前后发生的一种大规模全国性交通运输高峰期、高交通运输压力现象。已知某火车站候车厅，候车人数与时间 $t$ 相关，时间 $t$（单位：时）满足 $0<t\leq24$，$t\in\mathbb{N}$。经测算，当 $16\leq t\leq24$ 时，候车人数为候车厅满厅状态，满厅人数为 5160；当 $0<t<16$ 时，候车人数会减少，减少人数与 $t(16-t)$ 成正比，且时间为 6 点时，候车人数为 3960，记候车厅候车人数为 $f(t)$。||（1）求 $f(t)$ 的表达式，并求当天中午 12 点时，候车厅候车人数；||（2）若为了照顾群众的安全，每时需要提供的免费矿泉水瓶数为 $P=\frac{f(t)-3160}{t}+320$，则一天中哪个时间需要提供的矿泉水瓶数最少？
（1）$f(t)=\begin{cases}5160-20t(16-t), & 0<t<16, \\ 5160, & 16\leq t\leq24,\end{cases}$（$t\in\mathbb{N}$），$f(12)=4200$；（2）$t=10$ 时 || 解析：（1）当 $0<t<16$ 时，设 $f(t)=5160-kt(16-t)$（候车减少的人数与 $t(16-t)$ 成正比），$f(6)=3960$，则 $5160-k\cdot6\cdot(16-6)=3960$，即 $5160-60k=3960$，解得 $k=20$。$\therefore f(t)=\begin{cases}5160-20t(16-t), & 0<t<16, \\ 5160, & 16\leq t\leq24.\end{cases}$（$t\in\mathbb{N}$）。$f(12)=5160-20\times12\times4=5160-960=4200$。故当天中午 12 点时，候车厅候车人数为 4200。 ||（2）$P=\frac{f(t)-3160}{t}+320$。当 $0<t<16$ 时，$P=\frac{5160-20t(16-t)-3160}{t}+320=\frac{2000-320t+20t^2}{t}+320=20t+\frac{2000}{t}$。由基本不等式，$20t+\frac{2000}{t}\geq2\sqrt{20t\cdot\frac{2000}{t}}=2\sqrt{40000}=400$，当且仅当 $20t=\frac{2000}{t}$，即 $t^2=100$，$t=10$（$t>0$）时等号成立。当 $16\leq t\leq24$ 时，$P=\frac{5160-3160}{t}+320=\frac{2000}{t}+320\geq\frac{2000}{24}+320\approx83.33+320=403.33>400$。所以当 $t=10$ 时，需要提供的矿泉水瓶数最少。
                """}
            ]
        )
    ]
    response = llm.invoke(messages)
    return response.content