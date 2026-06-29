# 一级标题

## 二级标题

**加粗**  
*斜体*

* 无序列表项

1. 有序列表项  
   [链接文字](目标笔记.md)  
   ![图片描述](图片路径.png)  
   `行内代码`

````
````

### 1.3 双向链接

* 创建另一篇笔记，叫 `RAG 技术简介`。
* 在 `Obsidian入门` 中输入 `[[RAG 技术简介]]`，Obsidian 会自动链接。
* 点击这个链接可以跳转到那篇笔记，反过来，`RAG 技术简介` 中会显示“出链”和“反链”。
  [RAG 技术简介](RAG%20%E6%8A%80%E6%9C%AF%E7%AE%80%E4%BB%8B.md)

### 1.4 标签

* 在笔记任意位置输入 `#rag` 或 `#学习/obsidian`。
* 标签可以嵌套（`#父/子`），点击标签可以搜索所有带同样标签的笔记。

## 导出目录结构的方法

### 方法一：使用命令行（推荐，最清晰）

**Windows（PowerShell）**：

powershell

````
# 进入你的 MyKnowledge 目录
cd C:\你的路径\MyKnowledge

# 导出目录树结构（忽略 .obsidian 配置文件夹）
tree /F /A > 目录结构.txt
````

---

## 🔍 澄清：两种“Export to Markdown”

|名称|类型|用途|适用场景|
|--|--|--|----|
|**obsidian-export**|命令行工具（CLI）|将整个 Obsidian 库导出为纯净 Markdown|批量导出、自动化脚本、RAG 预处理|
|**Obsidian markdown export**|Obsidian 社区插件|在 Obsidian 界面内一键导出|偶尔导出单篇或单文件夹|

你在步骤 4 中问的，应该是指**前者**（obsidian-export 命令行工具），因为它更适合 RAG 场景的批量导出和自动化。

---

## 📦 方法一：安装 obsidian-export（命令行工具，推荐）

### 第 1 步：安装 Rust 环境

obsidian-export 是用 Rust 编写的，需要通过 Cargo 安装。

**Windows：**

1. 访问 https://rustup.rs/
1. 下载 `rustup-init.exe` 并运行
1. 按提示安装（默认选项即可）
1. 安装完成后，**重启 PowerShell**

**Mac / Linux：**

````bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env
````

### 第 2 步：通过 Cargo 安装 obsidian-export

````bash
cargo install obsidian-export
````

### 第 3 步：验证安装

````bash
obsidian-export --version
````

如果显示版本号（如 `obsidian-export 23.12.0`），安装成功。

### 第 4 步：导出你的知识库

````bash
# 基本命令格式
obsidian-export /path/to/your/vault /path/to/output

# 你的实际路径示例（Windows PowerShell）
obsidian-export D:\MyKnowledge D:\MyKnowledge_Export

# 可选：去除 frontmatter（如果 RAG 不需要）
obsidian-export D:\MyKnowledge D:\MyKnowledge_Export --frontmatter=never
````

导出后，`D:\MyKnowledge_Export` 里就是**纯净的 Markdown 文件**，`[[双链]]` 会被转换成标准链接格式。

---

## 🔌 方法二：安装 Obsidian 社区插件（界面操作）

如果你想在 Obsidian 界面里手动导出，可以安装社区插件：

### 安装步骤：

1. 打开 Obsidian → **设置**（左下角齿轮图标）
1. 左侧菜单选择 **第三方插件** → 关闭 **安全模式**
1. 点击 **浏览** 按钮
1. 搜索 **`markdown export`**
1. 找到 `Obsidian markdown export` 插件 → 点击 **安装**
1. 安装后点击 **启用**

### 使用方法：

* 右键点击任意笔记或文件夹 → **Export to Markdown**
* 或通过命令面板（`Ctrl+P`）搜索 `Export to Markdown`
* 设置输出路径（支持绝对路径，如 `D:\Export`）

---

## 📊 两种方式对比

|特性|obsidian-export (CLI)|Obsidian markdown export (插件)|
|--|---------------------|-----------------------------|
|**批量导出**|✅ 支持整个库|✅ 支持文件夹/多选|
|**自动化脚本**|✅ 适合|❌ 需手动操作|
|**链接转换**|✅ 智能处理|✅ 支持|
|**安装复杂度**|需装 Rust|直接在 Obsidian 内安装|
|**RAG 推荐度**|⭐⭐⭐⭐⭐|⭐⭐⭐|

---

## ✅ 针对你的情况建议

你已经有一个结构良好的 `MyKnowledge/` 知识库，**推荐使用方法一（obsidian-export CLI）**，因为：

1. 可以写入脚本实现**定期自动备份**
1. 导出结果更干净，方便 RAG 索引
1. 与后续阶段 2 的 Python 脚本集成更顺畅

---

## 📝 你现在需要做的

1. **安装 Rust**（约 5 分钟）
1. **运行 `cargo install obsidian-export`**（约 3 分钟）
1. **测试导出**：`obsidian-export D:\MyKnowledge D:\MyKnowledge_Export`
1. 告诉我导出是否成功，然后我们继续**阶段 2**

`obsidian-export D:\helen\workspace\repositories\brain\MyKnowledge D:\helen\workspace\repositories\RAG_System\data\raw\ai_assistant\MyKnowledge_Export`

\#学习/obsidian
