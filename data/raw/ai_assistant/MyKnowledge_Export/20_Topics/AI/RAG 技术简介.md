# RAG 技术简介

正文内容...

# RAG 从零到一：AI 小白的理论与实践教程

 > 
 > 作者：覃益佳  
 > 适合人群：对 AI 感兴趣、想了解 **RAG** 但零基础的同学  
 > 学习方式：理论 → 场景 → 提示词 → 动手实践

---

## 一、RAG 是什么？用一个故事讲清楚

**RAG = Retrieval-Augmented Generation**（检索增强生成）

想象你参加一个开卷考试：

* **传统大模型**：闭卷考试，只能靠脑子里记过的知识（训练数据）答题。如果问“2024 年诺贝尔和平奖得主是谁”，它可能答不出。
* **RAG**：开卷考试，先快速翻书（检索），找到相关内容，再结合找到的资料写出答案。

**官方定义**：  
RAG 先根据用户问题，从一个外部知识库（向量数据库、搜索引擎、文档库）中**检索**相关片段，再把这些片段和原问题一起交给大模型**生成**回答。

**核心价值**：  
✅ 解决大模型“不知道最新信息”的问题  
✅ 防止大模型“胡编乱造”（减少幻觉）  
✅ 让模型回答基于**你私有的资料**（公司文档、个人笔记、法律合同…）

---

## 二、RAG 的完整工作流程（必懂）

````mermaid
graph LR
    Q[用户问题] --> R[检索器 Retrieval]
    K[知识库] --> R
    R --> C[相关片段]
    C --> P[提示词组装]
    Q --> P
    P --> L[大模型 LLM]
    L --> A[最终答案]
````

**拆解为 4 步**：

1. **准备知识库**  
   把你的文档（PDF、网页、Markdown）切成短块（chunk），转成向量存入向量数据库。

1. **检索**  
   用户提问 → 把问题也转成向量 → 在数据库中找最相似的几个文档块。

1. **组装提示词**
   
   ````text
   基于以下资料回答问题：
   资料：{检索到的片段}
   问题：{用户问题}
   回答：
   ````

1. **生成**  
   大模型根据资料生成答案，如果资料里没有就明确说“不知道”。

---

## 三、零基础必须掌握的 5 个核心概念

|概念|通俗解释|为什么重要|
|--|----|-----|
|**Embedding（向量化）**|把文字转成一串数字（向量），比如“苹果”变成 \[0.12, -0.34, 0.87…\]|计算机才能比较文字之间的“语义相似度”|
|**向量数据库**|专门存向量并提供相似搜索的仓库（例如 Chroma、FAISS、Pinecone）|高效检索|
|**Chunk（文档分块）**|把长文档切成小段落，每段几百字|模型一次能读的内容有限，小块更精准|
|**Top-K**|只取最相似的 K 个片段（通常 3~5 个）|避免信息过载，节省成本|
|**Prompt 模板**|告诉模型“用这些资料来回答问题”的一段固定话术|控制模型行为，核心技巧|

---

## 四、提示词实战：从“无效”到“有效”的 RAG 提示词

### ❌ 错误示范（没有引导模型）

````
问题：什么是 RAG？
资料：{检索结果}
回答：
````

👉 模型可能忽略资料，自己瞎编。

### ✅ 基础有效版

````
你是一个严谨的问答助手。请**只根据**以下【资料】回答问题。  
如果资料里没有答案，请直接说“根据现有资料无法回答”。  
不要使用你自己的额外知识。

【资料】  
{chunk1}  
{chunk2}  
{chunk3}

【问题】  
{用户问题}

【回答】
````

### ✅ 进阶版（带引用和分点）

````
请基于【资料】回答问题。要求：
1. 答案必须来自资料，不得编造。
2. 每个结论后面用 [来源1] 标出对应资料编号。
3. 分点列出答案，要清晰。

【资料】
[1] {chunk1}
[2] {chunk2}

【问题】  
{问题}

【回答】
````

### ✅ 防幻觉强化版

````
如果资料足够且一致 → 生成准确答案。  
如果资料冲突 → 指出存在矛盾，并分别列出双方观点。  
如果资料部分相关 → 只回答可证实的部分，其余说“未找到足够信息”。  
如果完全不相关 → 回复“抱歉，我没有相关材料回答这个问题”。
````

---

## 五、动手实践：用 10 行代码跑通第一个 RAG

 > 
 > 使用 Python + 免费开源库，无需 GPU，普通电脑即可运行

### 环境准备（一键安装）

````bash
pip install chromadb langchain sentence-transformers openai
````

 > 
 > 注意：如果你没有 OpenAI 的 key，可以用本地模型替代（见文末常见问题）

### 完整示例代码

````python
# 1. 导入组件
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter

# 2. 加载你的小文档（假设你有一个 test.txt）
loader = TextLoader("./test.txt", encoding="utf-8")
documents = loader.load()

# 3. 分块（每块 300 字，重叠 50 字）
text_splitter = CharacterTextSplitter(chunk_size=300, chunk_overlap=50)
docs = text_splitter.split_documents(documents)

# 4. 生成向量并存入数据库
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh")  # 中文模型
vectorstore = Chroma.from_documents(docs, embeddings)

# 5. 检索 + 生成（此处用一个模拟函数，实际换成 OpenAI 或本地模型）
def simple_rag(question):
    # 检索 top-2 相关片段
    retrieved_docs = vectorstore.similarity_search(question, k=2)
    context = "\n\n".join([doc.page_content for doc in retrieved_docs])
    
    # 组装提示词（如果你有 GPT key，这里替换成 API 调用）
    prompt = f"""基于资料回答问题：
资料：{context}
问题：{question}
答案："""
    print("=== 提示词 ===\n", prompt)
    # 这里需要实际调用 LLM，见下面例子
    return prompt

# 测试
print(simple_rag("什么是 RAG？"))
````

### 换成调用 OpenAI（需要 API key）

````python
import openai
openai.api_key = "sk-xxx"

def rag_with_gpt(question):
    docs = vectorstore.similarity_search(question, k=3)
    context = "\n".join([d.page_content for d in docs])
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "只根据资料回答，不知道就说不知道。"},
            {"role": "user", "content": f"资料：{context}\n问题：{question}"}
        ]
    )
    return response.choices[0].message.content
````

---

## 六、进阶技巧（了解即可，未来有用）

|技巧|作用|难度|
|--|--|--|
|**HyDE**|先让模型生成一个假设答案，再用它去检索|⭐⭐|
|**ReRank**|第一次检索后，用更精密的模型重新排序|⭐⭐|
|**多路检索**|同时用关键词搜索 + 向量搜索，合并结果|⭐⭐|
|**Agentic RAG**|让模型自己决定什么时候检索、检索什么|⭐⭐⭐⭐|
|**Self-RAG**|让模型反思“我是否需要检索”“检索的结果是否够好”|⭐⭐⭐⭐|

---

## 七、常见问题（初学者必看）

**Q1：没有 OpenAI key 怎么办？**  
→ 使用 Ollama 运行本地模型（如 llama3、qwen），完全免费且隐私安全。  
示例：`ollama run qwen:7b`

**Q2：为什么我的 RAG 答案很差？**  
→ 常见原因：

* 分块太大或太小（建议 200~500 字）
* 检索到的片段不相关（减少 k 值或换 embedding 模型）
* 提示词没有强制约束（用“只根据资料”）

**Q3：中文用什么 embedding 模型？**  
推荐：`BAAI/bge-large-zh`、`moka-ai/m3e-base`、`text2vec-large-chinese`

**Q4：向量数据库怎么选？**

* 学习用：Chroma（纯 Python）
* 生产小规模：FAISS、Qdrant
* 生产大规模：Milvus、Pinecone

---

## 八、课后作业（完成即可算入门）

**作业 1**：用自己的一个文本文档（日记、笔记、公司手册任选）实现 RAG，问 3 个只有文档里才有答案的问题。  
**作业 2**：修改 top-k 从 1 到 5，观察答案变化。  
**作业 3**：写一段提示词，要求模型在答案末尾加上“——根据文档检索结果生成”。

**验收标准**：

* 模型能正确回答基于文档的问题
* 对于文档不存在的信息，模型回答“不知道”而不是编造

---

## 九、学习资源推荐（无广）

* 视频：李宏毅《生成式 AI 导论》中 RAG 章节
* 论文原文（可选）：*Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*
* 开源项目：LangChain 官方文档的 RAG 教程、LlamaIndex 入门

---

 > 
 > **最后一句真心话**：  
 > RAG 没有你想象的那么难——它就是一个 **“翻书 → 抄答案”** 的自动化流程。  
 > 你不需要成为算法专家，只要学会 **分块、向量化、写提示词** 这 3 件事，就能做出有用的应用。  
 > 试着跑通上面的代码，你会发现自己已经超越了 80% 的 AI 入门者。

覃益佳  
2025 年 3 月
