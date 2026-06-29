## GLM-5.1 Coding Plan 与 API Key 调用详解

是的，**GLM Coding Plan 包含 API Key 的调用**。让我为你详细解释这个套餐的机制和注意事项。

### 一、什么是 GLM Coding Plan？

GLM Coding Plan 是智谱 AI 针对**代码编程场景**推出的专属套餐。这个套餐的特点：

|特性|说明|
|--|--|
|**适用场景**|代码生成、代码解释、编程助手等 Coding 场景|
|**专属端点**|`https://open.bigmodel.cn/api/coding/paas/v4`|
|**通用端点**|`https://open.bigmodel.cn/api/paas/v4`（普通对话）|

**重要提醒**：Coding API 端点**仅限 Coding 场景**，并不适用通用 API 场景，请区分使用。

### 二、套餐到期时的错误处理（重要！）

如果你的 GLM Coding Plan 套餐已到期，API 会返回明确的错误码，告诉你需要续订：

````json
{
    "error": {
        "code": "1309",
        "message": "您的 GLM Coding Plan 套餐已到期，暂无法使用，前往官方续订后即可恢复 https://bigmodel.cn/claude-code"
    }
}
````

**解决方案**：

* 前往 [https://bigmodel.cn/claude-code](https://bigmodel.cn/claude-code) 续订套餐
* 续订后即可恢复使用

### 三、完整的 API 调用代码（含 API Key）

下面是区分 Coding 端点和通用端点的完整代码示例：

#### 方式一：使用 Coding 专属端点（推荐编程场景）

````python
import requests
import json

# ============================================================
# GLM-5.1 Coding Plan 配置
# ============================================================
API_KEY = "YOUR_API_KEY"  # 替换为你的智谱 API Key

# 注意：Coding 场景必须使用这个专属端点
CODING_API_URL = "https://open.bigmodel.cn/api/coding/paas/v4/chat/completions"

def coding_plan_chat(user_message):
    """使用 Coding Plan 套餐调用 GLM-5.1"""
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {API_KEY}'
    }
    
    data = {
        "model": "glm-5.1",
        "messages": [
            {"role": "system", "content": "你是一个专业的编程助手，擅长代码生成和解释。"},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.3,   # 编程场景建议较低温度，让输出更确定
        "max_tokens": 2000
    }
    
    try:
        response = requests.post(CODING_API_URL, headers=headers, json=data)
        result = response.json()
        
        if response.status_code == 200:
            return result['choices'][0]['message']['content']
        elif response.status_code == 401:
            return "❌ API Key 无效或已过期，请检查"
        elif result.get('error', {}).get('code') == '1309':
            return "❌ GLM Coding Plan 套餐已到期，请前往续订：https://bigmodel.cn/claude-code"
        else:
            return f"❌ 错误码 {response.status_code}: {result}"
            
    except Exception as e:
        return f"调用失败: {str(e)}"

# 使用示例
response = coding_plan_chat("请用 Python 实现一个快速排序算法")
print(response)
````

#### 方式二：使用通用端点（非编程场景）

````python
# 普通对话场景使用通用端点
GENERAL_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"  # 不是 coding 子域名

def general_chat(user_message):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {API_KEY}'
    }
    
    data = {
        "model": "glm-5.1",
        "messages": [
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.8
    }
    
    response = requests.post(GENERAL_API_URL, headers=headers, json=data)
    return response.json()
````

### 四、API Key 安全最佳实践

根据智谱官方文档，**不要直接把 API Key 硬编码在代码中**。推荐以下方式：

#### 方式一：使用环境变量（推荐）

````bash
# 在终端设置环境变量（Mac/Linux）
export ZHIPU_API_KEY="your_actual_api_key_here"

# Windows (CMD)
set ZHIPU_API_KEY=your_actual_api_key_here

# Windows (PowerShell)
$env:ZHIPU_API_KEY="your_actual_api_key_here"
````

````python
import os

API_KEY = os.environ.get("ZHIPU_API_KEY")
if not API_KEY:
    raise ValueError("请设置环境变量 ZHIPU_API_KEY")
````

#### 方式二：使用 .env 文件

````bash
# 创建 .env 文件
ZHIPU_API_KEY=your_actual_api_key_here
````

````python
from dotenv import load_dotenv
import os

load_dotenv()  # 加载 .env 文件
API_KEY = os.getenv("ZHIPU_API_KEY")
````

#### 方式三：使用配置文件（记得加入 .gitignore）

````python
# config.py - 不要提交到 Git！
API_KEY = "your_actual_api_key_here"
````

### 五、常见错误码及解决方案

针对 GLM Coding Plan 可能遇到的错误：

|错误码|含义|解决方案|
|---|--|----|
|**401**|鉴权失败|检查 API Key 是否正确|
|**1309**|Coding Plan 套餐到期|前往续订套餐|
|**1311**|当前套餐未开放模型权限|升级套餐或联系客服|
|**1312**|模型访问量过大|稍后重试或切换其他模型|
|**429**|请求频率过高|降低请求频率|

### 六、完整示例：集成到 RAG 系统

回到我们之前的 RAG 教程，这是整合了 Coding Plan 的正确调用方式：

````python
def ask_glm5_with_coding_plan(question, context):
    """
    使用 GLM Coding Plan 端点调用 GLM-5.1
    适用于编程问答、代码生成等场景
    """
    # Coding Plan 专属端点
    CODING_API_URL = "https://open.bigmodel.cn/api/coding/paas/v4/chat/completions"
    
    # 从环境变量读取 API Key
    API_KEY = os.environ.get("ZHIPU_API_KEY")
    
    system_prompt = """你是一个严谨的编程问答助手。请**只根据**以下【资料】回答问题。
如果资料里没有答案，请直接说"根据现有资料无法回答"。
不要使用你自己的额外知识，不要编造。"""

    user_prompt = f"""【资料】
{context}

【问题】
{question}

【回答】"""

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    payload = {
        "model": "glm-5.1",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 1000
    }
    
    response = requests.post(CODING_API_URL, headers=headers, json=payload)
    result = response.json()
    
    # 处理套餐到期的特殊情况
    if result.get('error', {}).get('code') == '1309':
        return "⚠️ GLM Coding Plan 套餐已到期，请前往 https://bigmodel.cn/claude-code 续订"
    
    return result['choices'][0]['message']['content']
````

### 总结

|要点|说明|
|--|--|
|**是否包含 API Key 调用**|✅ 是的，Coding Plan 需要 API Key 鉴权|
|**专属端点**|`https://open.bigmodel.cn/api/coding/paas/v4/chat/completions`|
|**套餐到期错误码**|`1309`|
|**续订地址**|[https://bigmodel.cn/claude-code](https://bigmodel.cn/claude-code)|
|**安全建议**|使用环境变量，不要硬编码|

有任何问题欢迎继续交流！
