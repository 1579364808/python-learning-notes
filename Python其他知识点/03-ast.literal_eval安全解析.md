# ast.literal_eval 安全解析

## 一句话总结

把字符串形式的 Python 字面量（列表、字典等）安全地解析为真正的 Python 对象，比 `eval()` 安全。

## 要点

- 只解析字面量：`str`、`int`、`float`、`list`、`dict`、`tuple`、`bool`、`None`
- 不会执行代码，比 `eval()` **安全**
- 常用于解析 LLM 返回的结构化文本

## 示例

```python
import ast

# 字符串 → 列表
text = '["步骤1", "步骤2"]'
plan = ast.literal_eval(text)
# plan = ["步骤1", "步骤2"]
# type(plan) → <class 'list'>

# 字符串 → 字典
d = ast.literal_eval('{"name": "Alice", "age": 25}')
# d = {"name": "Alice", "age": 25}

# eval() 可以执行任意代码，危险
eval("__import__('os').system('ls')")  # ❌ 危险！

# literal_eval 会直接报错
ast.literal_eval("__import__('os').system('ls')")  # ✅ 抛 ValueError
```

## 对比

| 函数 | 安全性 | 用途 |
|------|--------|------|
| `eval()` | ❌ 危险，可执行代码 | 永远不要用 |
| `ast.literal_eval()` | ✅ 安全，只解析字面量 | 解析 LLM 输出、配置文件 |
| `json.loads()` | ✅ 安全，但只支持 JSON | 解析 JSON 数据 |
