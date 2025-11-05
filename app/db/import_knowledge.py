import sys
import pathlib
import pandas as pd
from sqlalchemy import text

PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.db.session import engine

EXCEL_PATH = PROJECT_ROOT / "docs" / "知识点.xlsx"
SHEET_NAME = "Sheet1"

df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME, dtype=str)
df = df.dropna(how='all')
df = df.fillna("")

for col in ['function_type', 'function_property', 'name', 'content']:
    if col in df.columns:
        df[col] = df[col].astype(str).str.replace('\r\n', '；').str.replace('\n', '；').str.replace('\r', '；')
        df[col] = df[col].str.strip()

if (df['name'] == "").any():
    raise ValueError("存在name为空的记录！")

if df['name'].duplicated().any():
    dup_names = df[df['name'].duplicated()]['name'].unique()
    raise ValueError(f"name不唯一！重复项：{dup_names}")

if (df['content'] == "").any():
    raise ValueError("存在content为空的记录")

print("数据校验通过")

with engine.connect() as conn:
    conn.execute(text("DELETE FROM knowledge_nodes"))
    conn.commit()

columns_to_insert = ['function_type', 'function_property', 'name', 'content']
df_to_insert = df[columns_to_insert]
df_to_insert = df_to_insert.replace('', None)
df_to_insert.to_sql("knowledge_nodes", engine, if_exists="append", index=False, method="multi")

print(f"✅ 成功写入 {len(df_to_insert)} 条知识点！")