# 步骤 3：为 RAG 准备笔记别名和元数据

## 1. Frontmatter（YAML 头信息）

* 位置：笔记最顶部，用 `---` 包裹
* 作用：存储结构化元数据，供 Obsidian 和 RAG 系统读取

## 2. 别名（aliases）

* 语法：`aliases: [别名1, 别名2]`
* 作用：RAG 检索时把别名当作等价关键词，提高召回
* 示例：`aliases: [检索增强生成, RAG, Retrieval-Augmented Generation]`

## 3. 推荐元数据字段

|字段|说明|
|--|--|
|title|正式标题|
|aliases|同义词/缩写|
|tags|分类标签|
|date|创建日期|
|status|成熟度（萌芽/草稿/完成）|
|type|笔记类型（概念/教程/问题）|
|source|信息来源|

## 4. 模板使用

* 在 `90_Templates/` 下创建 frontmatter 模板
* 新笔记用 `Ctrl/Cmd+T` 快速插入

## 5. 实际操作

已在 `RAG 技术简介.md` 中添加了包含 aliases 和 tags 的 frontmatter 示例。
