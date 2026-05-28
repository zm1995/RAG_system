# weixinchat 数据源

将微信答疑 Excel/CSV 放在此目录，需包含列（可在 `src/config.py` 修改映射）：

- `文字提问问题`：原问题
- `文本解答`：原答案

处理命令：

```bash
python -m src.pipelines.generate_export --source weixinchat
```
