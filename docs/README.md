

# 📘 智能数学题库与知识图谱系统

本项目旨在构建一个**结构化的中学数学题库系统**，支持题目管理、知识点标注与可视化知识图谱构建，为智能答疑、个性化推荐或教学分析提供数据基础。

## 🌟 核心功能

- 📝 **结构化题目存储**：支持题目文本、答案解析、难度标签与知识点标签。
- 🏷️ **标准化知识点体系**：基于函数类型（如二次函数、三角函数）与函数性质（如单调性、奇偶性）进行双重标注。
- 🖼️ **题目/解析图片管理**：支持题目与解析中嵌入图片，独立存储与关联。
- 🧠 **知识图谱构建**：将知识点间的关系（如“先修”“依赖”）导入 Neo4j，实现可视化探索。
- 🔍 **数据清洗与去重**：通过归一化处理（或可选向量比对）减少题目重复。

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

### 4. 启动服务

`python run.py`

默认运行在 `http://localhost:8000`。

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

本项目通过 `.env` 文件管理敏感信息（如 Neo4j 密码）。请复制 `.env.example` 为 `.env` 并填入你的实际配置。
**切勿将 `.env` 提交至版本控制！** 