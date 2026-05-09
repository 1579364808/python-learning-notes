# 条件判断与 `all()` 函数对比：Java vs Python

## 代码对比

```python
# Python: all() 检查所有元素是否为 True
if not all([self.model, self.apiKey, self.baseUrl]):
    raise ValueError("缺少必要参数")
```

```java
// Java: 需要逐个判断每个字段
if (this.model == null || this.apiKey == null || this.baseUrl == null) {
    throw new IllegalArgumentException("缺少必要参数");
}
```

## 差异表格

| 对比项 | Python | Java |
|--------|--------|------|
| 批量空值检查 | `all([a, b, c])` 一行搞定 | 需要 `\|\|` 逐个判断 |
| 短路求值 | `all()` 内部会短路 | Java 的 `\|\|` 也有短路 |
| "假值"范围 | `None`, `""`, `0`, `[]`, `False` 都算假 | 只有明确 `== null` |
| 语义 | "所有值都真才通过" | "任何一个为 null 就抛异常" |

## 要点说明

1. **`all()` 是 Python 内置函数**，接收一个可迭代对象，所有元素为真才返回 `True`，任意一个为假就返回 `False`
2. **`not` 取反** —— "如果不是全都为真" = "只要有一个是假的"
3. **Python 的"假值"比 Java 多**：`None`、空字符串 `""`、数字 `0`、空列表 `[]`、空字典 `{}`、`False` 都是假。所以 `all()` 比 Java 的 `== null` 检查更严格
4. **等价展开**：`if not all([self.model, self.apiKey, self.baseUrl])` 相当于：
   ```python
   if not self.model or not self.apiKey or not self.baseUrl:
   ```
