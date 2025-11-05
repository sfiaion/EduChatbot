### users 用户表

| 字段名        | 类型      | 是否可以为空 | 说明                            |
| ------------- | --------- | ------------ | ------------------------------- |
| id            | Integer   | 否           | 主键                            |
| phone         | String    | 否           | 唯一，用作用户名，登录凭证      |
| password_hash | String    | 否           | 密文密码                        |
| email         | String    | 是           | 邮箱                            |
| role          | String    | 是           | 枚举，student/teacher/（admin） |
| is_active     | Boolean   | 否           | 账号是否启用，默认True          |
| created_at    | TIMESTAMP | 否           | 注册时间                        |

### students 学生表

| 字段名         | 类型    | 是否可以为空 | 说明               |
| -------------- | ------- | ------------ | ------------------ |
| id             | Integer | 否           | 主键               |
| user_id        | Integer | 否           | 用户表外键         |
| student_number | String  | 否           | 在班级内唯一，学号 |
| name           | String  | 否           | 真实姓名           |
| class_id       | Integer | 是           | 班级表外键         |

### teachers 教师表

| 字段名  | 类型    | 是否可以为空 | 说明       |
| ------- | ------- | ------------ | ---------- |
| id      | Integer | 否           | 主键       |
| user_id | Integer | 否           | 用户表外键 |
| name    | String  | 否           | 真实姓名   |

### classes 班级表

| 字段名     | 类型    | 是否可以为空 | 说明       |
| ---------- | ------- | ------------ | ---------- |
| id         | Integer | 否           | 主键       |
| name       | String  | 否           | 班级名称   |
| teacher_id | Integer | 否           | 教师表外键 |

### questions 题目表

| 字段名              | 类型      | 是否可以为空 | 说明                                                         |
| ------------------- | --------- | ------------ | ------------------------------------------------------------ |
| id                  | Integer   | 否           | 主键                                                         |
| question            | String    | 否           | 题目文本                                                     |
| normalized_question | String    | 否           | 唯一，完全处理后的题目                                       |
| answer              | String    | 否           | 答案解析文本                                                 |
| knowledge_tag       | JSON      | 否           | 二维知识点列表，<br/>{<br/>  "function_types": [],<br/>  "function_properties": []<br/>} |
| difficulty_tag      | String    | 否           | 难度等级，枚举值：easy/medium/hard                           |
| created_at          | TIMESTAMP | 否           | 时间戳                                                       |

function_types只能从以下几个值中选择：分段函数，二次函数，幂函数，指数函数，对数函数，三角函数，复合函数

function_properties只能从以下几个值中选择：定义域与值域，单调性，最值，奇偶性与对称性，周期性，零点与方差

注：关于题目的去重与相似性判断，当前存在两种方案：

1. 基于归一化文本（normalized_question）：对题目进行标准化清洗（如去除多余空格、统一符号格式等），确保语义相同的题目生成相同的归一化字符串，用于精确去重。
2. 基于向量嵌入比对：将题目编码为语义向量，通过相似度阈值判断是否重复。

若选择向量方案，则应该在本文档和项目models中移除 normalized_question 字段；若保留文本归一化方案，则该字段继续作为去重依据。

### images 题目图片表

| 字段名      | 类型      | 是否可以为空 | 说明                                                    |
| ----------- | --------- | ------------ | ------------------------------------------------------- |
| id          | Integer   | 否           | 主键                                                    |
| question_id | Integer   | 否           | 题目表外键                                              |
| path        | String    | 否           | 存储路径                                                |
| image_type  | String    | 否           | 判断是题目中的图还是解析中的图，枚举值：question/answer |
| created_at  | TIMESTAMP | 否           | 时间戳                                                  |

注：关于图片与其上下文（题目正文或答案解析）的关联方式，当前存在两种方案：

1. 结构化字段标识（当前设计）：通过 image_type 字段显式标记图片属于 question 或 answer，便于程序逻辑判断和独立管理图片资源。
2. 文本内嵌引用：将图片路径以特定格式（如 [img:xxx.jpg]）直接嵌入 questions.question 或 questions.answer 字段中，通过解析文本提取图片信息。

若选择内嵌方案，则应该在本文档和项目models中移除 image_type 字段；若保留结构化字段方案，则该字段继续作为去重依据。

若最终选择**文本内嵌方案**，请注意：

- 文本字段需支持可靠解析（如约定格式、避免冲突）；
- 图片路径需全局唯一，且与存储系统解耦（比如用 UUID 命名）；
- 删除题目时需额外处理图片的级联清理（否则易产生孤儿文件）；
- 前端展示纯文本时应剔除图片标记。

### assignments 作业表

| 字段名                | 类型      | 是否可以为空 | 说明                   |
| --------------------- | --------- | ------------ | ---------------------- |
| id                    | Integer   | 否           | 主键                   |
| title                 | String    | 否           | 作业标题               |
| teacher_id            | Integer   | 否           | 教师表外键             |
| assigned_student_ids  | JSON      | 否           | 这份作业被推送给的学生 |
| assigned_question_ids | JSON      | 否           | 这份作业中包含的题目   |
| created_at            | TIMESTAMP | 否           | 创建时间               |

### student_submissions 学生作答表

| 字段名         | 类型      | 是否可以为空 | 说明         |
| -------------- | --------- | ------------ | ------------ |
| id             | Integer   | 否           | 主键         |
| question_id    | Integer   | 否           | 题目表外键   |
| student_id     | Integer   | 否           | 学生表外键   |
| assignment_id  | Integer   | 是           | 作业表外键   |
| student_answer | String    | 否           | 学生作答     |
| is_correct     | Boolean   | 是           | 默认值为NULL |
| created_at     | TIMESTAMP | 否           | 时间戳       |

### knowledge_nodes 知识图谱节点表

| 字段名            | 类型    | 是否可以为空 | 说明                                   |
| ----------------- | ------- | ------------ | -------------------------------------- |
| id                | Integer | 否           | 主键                                   |
| function_type     | String  | 是           | 函数类型，如指数函数                   |
| function_property | String  | 是           | 函数性质，如定义域                     |
| name              | String  | 否           | 唯一，具体名称，如”指数函数定义域“     |
| content           | String  | 否           | 内容，如”指数函数$y=a^x$的定义域是$R$“ |

### error_analysis 错误分析表

| 字段名            | 类型      | 是否可以为空 | 说明                                                  |
| ----------------- | --------- | ------------ | ----------------------------------------------------- |
| id                | Integer   | 否           | 主键                                                  |
| submission_id     | Integer   | 否           | 唯一，学生作答表外键                                  |
| error_type        | String    | 否           | 枚举值：knowledge/calculation/misreading/logic/method |
| analysis          | String    | 否           | 大模型生成的分析                                      |
| knowledge_node_id | Integer   | 是           | 知识节点表外键，仅知识点错误时非空                    |
| created_at        | TIMESTAMP | 否           | 时间戳                                                |

以下几个地方加了relationship:

Student and StudentSubmission

Question and StudentSubmission

StudentSubmission and ErrorAnalysis

ErrorAnalysis and KnowledgeNode

User and Student or Teacher

Teacher and Assignment