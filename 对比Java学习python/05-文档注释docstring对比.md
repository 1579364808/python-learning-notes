# 文档注释对比：Java vs Python

## 代码对比

```python
# Python: 文档字符串（docstring），用三重双引号
def call_llm():
    """
    调用大语言模型进行思考，并返回其响应。
    """
    pass

# 也可以用在类、模块的开头
class LlmClient:
    """大语言模型客户端"""
    pass
```

```java
// Java: Javadoc 注释，用 /** ... */
/**
 * 调用大语言模型进行思考，并返回其响应。
 */
public String callLlm() {
    return null;
}

// 或普通块注释（不推荐用于文档）
/*
 * 调用大语言模型进行思考
 */
```

## 差异表格

| 对比项 | Python | Java |
|--------|--------|------|
| 语法 | `"""..."""` 字符串（本质是表达式） | `/** ... */` 注释（编译时忽略） |
| 存储 | 运行时存在，可通过 `obj.__doc__` 访问 | 编译后不存在 |
| 标准格式 | 无强制格式（推荐 Google/NumPy 风格） | Javadoc 标签（`@param`、`@return`） |
| 多行注释替代 | docstring 同时充当多行注释 | `/* ... */` 块注释 |
| 访问方式 | `help(func)` 或 `func.__doc__` | IDE 悬停显示 |

## 示例对比

```python
def add(a: int, b: int) -> int:
    """返回两个数的和。"""
    return a + b

print(add.__doc__)  # 返回两个数的和。
```

```java
/**
 * 返回两个数的和。
 * @param a 第一个数
 * @param b 第二个数
 * @return a + b
 */
public int add(int a, int b) {
    return a + b;
}
```

## 要点说明

1. **`"""..."""` 本质是字符串**，不是注释 —— 它会被 Python 解释器当成一个表达式执行（只不过值没赋值给变量，所以没效果）
2. **函数/类/模块的第一行 `"""..."""` 会被自动识别为 docstring**，可以通过 `.__doc__` 拿到
3. **Java 的 `/** */` 是真正的注释**，编译后消失；Python 的 docstring 运行时还在
4. 常见的 docstring 风格有 Google 风格和 NumPy 风格，比 Java 的 `@param` 更简洁
