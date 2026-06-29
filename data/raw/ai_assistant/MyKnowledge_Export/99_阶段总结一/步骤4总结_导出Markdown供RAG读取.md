# 步骤 4：导出 Obsidian 库为纯 Markdown 文件供 RAG 读取

## 1. Obsidian 库本质已是 Markdown

* `.md` 文件可直接被 RAG 读取
* 需注意 `[[双向链接]]`、`![[图片]]` 等 Obsidian 特有语法

## 2. 建议的导出方式

|方式|优点|缺点|
|--|--|--|
|直接复制文件夹|简单、无需插件|需自行处理特殊语法|
|使用 Export to Markdown 插件|自动清理链接|需安装插件|

## 3. 特殊语法清理示例（Python）

````python
import re
content = re.sub(r'\[\[(.*?)\]\]', r'\1', content)  # [[笔记]] → 笔记
content = re.sub(r'!\[\[.*?\]\]', '', content)      # 移除图片嵌入
````
