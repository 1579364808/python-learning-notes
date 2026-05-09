# str.format() 花括号转义

## 一句话总结

`.format()` 用 `{}` 做占位符替换，如果要输出文字 `{}` 本身，用 `{{` 和 `}}` 转义。

## 要点

- `{var}` → 被 `.format(var=xxx)` 替换为实际值
- `{{var}}` → 保留为文字 `{var}`，不会被替换
- 这跟 Java 的 `String.format("%s", x)` 中 `%%` 转义 `%` 是同一个道理

## 示例

```python
template = "可用工具: {tools}"
template.format(tools="Search")
# 结果: "可用工具: Search"

template2 = "请输出: `{{tool_name}}[{{tool_input}}]`"
template2.format()
# 结果: "请输出: `{tool_name}[{tool_input}]`"

# 混合使用
template3 = "工具: {tools}  格式: `{{tool_name}}[{{tool_input}}]`"
template3.format(tools="Search")
# 结果: "工具: Search  格式: `{tool_name}[{tool_input}]`"
```

## 对比

| 模板写法 | .format() 结果 | 说明 |
|---------|---------------|------|
| `{name}` | 替换为 name 值 | 占位符 |
| `{{name}}` | `{name}` | 保留花括号 |
| `{{}}` | `{}` | 保留空花括号 |
