

# 📘 智能数学题库与知识图谱系统

本项目旨在构建一个**结构化的中学数学题库系统**，支持题目管理、知识点标注与可视化知识图谱构建，为智能答疑、个性化推荐或教学分析提供数据基础。

## 🌟 核心功能

- 📝 **结构化题目存储**：支持题目文本、答案解析、难度标签与知识点标签。
- 🏷️ **标准化知识点体系**：基于函数类型（如二次函数、三角函数）与函数性质（如单调性、奇偶性）进行双重标注。
- 🖼️ **题目/解析图片管理**：支持题目与解析中嵌入图片，独立存储与关联。
- 🧠 **知识图谱构建**：将知识点间的关系（如“先修”“依赖”）导入 Neo4j，实现可视化探索。
- 📚 **教材 RAG 增强问答**：基于人教版数学教材构建 RAG 知识库，利用 `Qwen-VL` 进行多模态 OCR 与语义切片，实现在线对话时的权威知识点对齐与证据追溯。
- 💬 **智能学习助手**：基于 DashScope (qwen-max) 的对话系统，内置安全边界，支持 **Markdown + LaTeX** 渲染，并集成 RAG 插件实现“有据可依”的回答。
- 🔍 **数据清洗与去重**：通过归一化处理（或可选向量比对）减少题目重复。


## 🔁 整体流程（端到端）

- 教师上传
  - 通过前端或 `POST /api/assignments/upload` 上传试卷图片（或 DOCX → PDF → 图片），系统解析题目与答案，生成作业与试题列表。
- 学生作答
  - 学生在前端逐题提交（文本或图片），后端记录为 `StudentSubmission`。
- 严格批改
  - 后端使用 LLM 对比学生答案与标准答案，严格判断是否正确。
  - 错题进行错误类型归类（计算/审题/逻辑/方法/知识点），并据题目标签候选识别知识点，将 `knowledge_node_id` 持久化到 `ErrorAnalysis`。
- 统计与推荐
  - 统计接口聚合正确率、错误类型分布、学生列表与弱项标签。
  - 错题推荐接口根据学生的错题与所关联的知识点，从向量索引（FAISS）中检索相似题或针对性练习。
- 教材 RAG 增强
  - **知识入库**：将图片版 PDF 教材通过 `Qwen-VL-Plus` 进行多模态 OCR 识别，并按语义单元（定义/定理/例题）进行切分，存入独立向量库。
  - **检索增强**：对话时根据用户提问，在 `rag_passages` 索引中召回最相关的教材原文，作为 Prompt 上下文注入，确保回答事实准确且课程对齐。
- 知识图谱分析
  - 断点：对每个知识点计算“本节点错误数 - 前驱最大错误数”，展示异常增长的薄弱点。
  - 候选：按错误数降序返回班级时间范围内的潜在中心知识点。
  - 节点详情：显示最长前置路径、每日错误趋势折线图、高频前置节点与内容（支持 LaTeX）。
- 前端体验
  - 教师端：上传、统计总览、学生列表、知识图谱、（可扩展）错题推荐入口。
  - 学生端：查看作业、提交作答、查看批改反馈与推荐题。

## 🛠️ 快速开始

### 1. 安装依赖

`pip install -r requirements.txt`

（我没有为这个项目单独创建虚拟环境，不确定`requirements`里面有没有遗漏，请根据实际`import`语句安装）

> 请确保已安装 Python 3.8+、SQLite（通常内置）及 Neo4j（用于知识图谱，可选）。 

### 2. 初始化数据库

`python app/db/init_db.py`

数据库文件将生成于 `app/db/school.db`。

### 3. 导入基础数据

导入预定义的知识点（如“二次函数”、“单调性”等）

`python -m app.db.import_knowledge`

**新增：**导入题库

`python -m app.db.import_question`

**新增：**导入向量（导入向量会生成 `faiss.index` 和 `id2vector.pkl` 两个文件，这两个文件已经上传了。如果需要重新导入，需要把已有的这两个文件删除）

`python -m app.db.import_vector`

**新增：构建 RAG 教材知识库**

1. 解析教材 PDF（需确保 `Poppler_PATH` 已配置）：
   `python app/scripts/ingest_textbook.py`
2. 生成 RAG 向量索引：
   `python app/db/import_rag_vector.py`

### 4. 启动服务

`python run.py`

默认运行在 `http://localhost:8000`。

### （新增）前端搭建与联调

1. 安装 Node.js（建议 18+ 或 20+），验证：
```
node -v
npm -v
```

2. 创建前端项目（在 `EduChatbot` 目录下）：
```
cd EduChatbot
npm create vite@latest frontend -- --template vue-ts
cd frontend
npm i
npm i axios pinia vue-router element-plus @antv/g6 echarts @vueuse/core dayjs marked dompurify katex
```

3. 设置前端环境变量（在 `EduChatbot/frontend` 新建 `.env.local`）：
```
VITE_API_BASE_URL=http://127.0.0.1:8000
```

4. 设置后端环境变量（在 `EduChatbot` 新建 `.env`）：
```
# Neo4j 配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# DashScope (通义千问) API Key
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
```

5. 配置开发代理（`EduChatbot/frontend/vite.config.ts`）：
```ts
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
export default defineConfig({
  plugins: [vue()],
  server: { proxy: { '/api': 'http://127.0.0.1:8000' } }
})
```

6. 运行前端开发服务：
```
npm run dev
```
默认地址：`http://localhost:5173/`

7. 页面与接口对应关系：
- `/chat` → `POST /api/chat`（流式 `text/plain`）
- `/knowledge` → `GET /api/knowledge-graph?center=...`
- `/problems` → `POST /api/problems/upload`
- `/ocr` → `POST /api/submissions/ocr`

8. 目录结构（示例）：
```
EduChatbot/
├─ app/                 # 后端
├─ frontend/            # 前端
│  ├─ src/app/          # main.ts、App.vue、router、store、styles
│  ├─ src/features/     # chat/knowledge/problems/submissions
│  ├─ src/services/     # apiClient.ts、modules/*
│  ├─ src/components/   # 通用组件
│  ├─ src/types/        # 共享类型
│  └─ vite.config.ts
└─ run.py
```

9. 💡 **公式渲染技术说明**（ChatPanel.vue）：
为了解决 Markdown 与 LaTeX 的语法冲突（如 `_` 转义、`$$` 分段），项目采用了 **“保护-解析-还原”** 策略：
1. **预处理**：将 `$$...$$`、`\[...\]`、`\(...\)` 等 LaTeX 公式替换为 `<math-block>` 占位符。
2. **Markdown 解析**：使用 `marked` 解析剩余文本（此时公式已被保护，不会被误解析）。
3. **还原**：将占位符替换回原始 LaTeX 代码。
4. **渲染**：使用 `katex` 本地依赖包中的 `renderMathInElement` 对最终 DOM 进行数学公式渲染（已移除 CDN 依赖，支持离线运行）。
> 注意：样式文件已在 `main.ts` 中全局引入。

10. Windows 常见问题：
- 若出现 npm 缓存权限错误（EPERM）：使用项目级缓存
```
npm --cache .npm-cache --no-progress --prefer-online <your command>
```
或设置全局缓存
```
npm config set cache "%USERPROFILE%\\.npm-cache"
```
- CORS 报错：确认后端允许 `http://127.0.0.1:5173`，前端代理指向 `http://127.0.0.1:8000`
- 流式未显示：检查后端 `StreamingResponse` 的 `media_type=text/plain` 与前端使用 `ReadableStream` 读取

### 5. 查看知识图谱（需 Neo4j 已启动并导入数据）

1. **安装 Java 17+**  
   Neo4j 5.x 要求 **Java 17 或更高版本**。  
   - 下载 OpenJDK：https://adoptium.net/  
   - 验证安装：`java -version`
2. **下载并启动 Neo4j Desktop 或 Community Server**  
   - 官网下载：https://neo4j.com/download/  
   - 启动后，默认访问：http://localhost:7474  
   - 默认账号：`neo4j`，首次登录需修改密码（请将新密码填入 `.env`）
3. 导入知识点关系到 Neo4j
   - `python -m app.db.import_graph`
   - `http://localhost:8000/static/display_knowledge_graph.html`

### （新增）6.下载模型

下载 `bert-base-chinese` （自动打标签那里需要）

下载 `shibing624/text2vec-base-chinese` （错题推荐那里需要）

可以参考`test/download.py`

### 教师上传题目

#### DOCX 转 PDF（LibreOffice

本项目使用 **LibreOffice（soffice.exe）** 将 `.docx` 文档转换为 `.pdf`。

##### 安装 LibreOffice（Windows）

1. 下载地址：
    https://www.libreoffice.org/download/download-libreoffice/

2. 安装后，默认路径大约如下：

   `C:\Program Files\LibreOffice\program\soffice.exe`

> ⚠️ LibreOffice **不是 pip 包**，但必须让在本地安装。

------

#### PDF 转图片（Poppler）

项目使用 `pdf2image` 将 PDF 转为 PNG。
 Windows 上需要额外安装 **Poppler**。

##### 安装 Poppler（Windows）

1. 下载 Windows 版 Poppler（第三方维护）：
    https://github.com/oschwartz10612/poppler-windows/releases/

2. 解压后，将路径指向解压目录的 `/bin`，例如：

   `D:\poppler\poppler-24.08.0\Library\bin`

3. 安装依赖：

   `pip install pdf2image`

### （新增）前端依赖与配置说明

- Node 版本：建议使用 `Node.js 18` 或 `20`
- 包管理：使用 `npm`（生成并提交 `package-lock.json` 以锁定依赖）
- 前端主要依赖：
  - 运行时：`vue`、`pinia`、`vue-router`、`axios`、`element-plus`、`@antv/g6`、`echarts`、`@vueuse/core`、`dayjs`
  - 构建与类型：`vite`、`@vitejs/plugin-vue`、`typescript`、`@vue/tsconfig`、`vue-tsc`
- 常用脚本：
  - 开发：`npm run dev`
  - 构建（含 TS 类型检查）：`npm run build`
  - 预览构建产物：`npm run preview`
- 环境变量（`EduChatbot/frontend/.env.local`）：
  - `VITE_API_BASE_URL=http://127.0.0.1:8000`
- 代理与路径别名（`EduChatbot/frontend/vite.config.ts`）：
  - 代理：`/api → http://127.0.0.1:8000`
  - 别名：`@ → src`
- 首次安装：
  - `cd EduChatbot/frontend && npm i`
  - 如已有锁文件，优先使用 `npm ci` 保证安装一致性

### （新增）版本控制：提交与忽略清单

- 建议提交（必须或应当提交到仓库）：
  - 后端代码：`EduChatbot/app/**`（不含本地 `.env` 与生成文件）
  - 前端代码：`EduChatbot/frontend/src/**`、`index.html`、`vite.config.ts`
  - 依赖清单与锁：`EduChatbot/requirements.txt`、`EduChatbot/frontend/package.json`、`EduChatbot/frontend/package-lock.json`
  - 配置：`tsconfig*.json`、`.vscode/extensions.json`（可选）
  - 文档与脚本：`EduChatbot/docs/**`、`run.py`、测试脚本 `test/**`

- 必须忽略（不提交）：
  - 虚拟环境与缓存：`.venv/`、`venv/`、`.npm-cache/`
  - 依赖目录：`EduChatbot/frontend/node_modules/`
  - 构建产物：`EduChatbot/frontend/dist/`
  - 环境文件：`.env`、`.env.local`、`.env.production`
  - 本地数据库与大型生成文件：`EduChatbot/app/db/*.db`、`EduChatbot/app/db/*.sqlite`、`faiss.index`、`id2vector.pkl`
  - 临时/系统文件：`tmp/`、`.DS_Store`、`*.log`

> 说明：锁文件 `package-lock.json` 应提交，以确保团队安装一致；环境文件与本地数据库不应提交，按 README 初始化即可复现环境。

## 🧪 开发与调试工具

- **查看数据库**：

  `sqlite3 app/db/school.db`

- **查询特定知识点**（验证是否导入成功）：

  `python -m test.check_knowledge`

- **前端渲染测试**
  项目提供一个简易 HTML 测试页面：

  `open test/check_knowledge.html`

  你可将知识点、题目文本或答案解析内容临时粘贴到该页面中，快速验证：

  - 文本是否正常显示（无乱码）
  - 数学公式、特殊符号渲染是否正确
  - 换行、空格、中文标点等格式是否保留
    该页面模拟了实际前端展示环境，适合在开发初期快速排查显示问题。

- **（新增）导入测试数据**

  `python -m mock_errors` 和 `python_mock_students_and_submissions` 可以在学生表，学生作答表和错误分析表中填写测试数据

## 🔐 **敏感配置**

**切勿将 `.env` 提交至版本控制！**
