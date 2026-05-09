# `join` 方法：字符串拼接对比

## Python `str.join()` vs Java `String.join()`

```python
# Python
collected = ["hello", "world", "python"]
result1 = "".join(collected)      # "helloworldpython"
result2 = ", ".join(collected)    # "hello, world, python"
result3 = " | ".join(collected)   # "hello | world | python"
```

```java
// Java
List<String> collected = List.of("hello", "world", "python");
String result1 = String.join("", collected);      // "helloworldpython"
String result2 = String.join(", ", collected);    // "hello, world, python"
String result3 = String.join(" | ", collected);   // "hello | world | python"
```

## 差异表格

| 对比项 | Python | Java |
|--------|--------|------|
| 调用方式 | `"分隔符".join(可迭代对象)` | `String.join("分隔符", 集合)` |
| 连接符位置 | 字符串字面量上调用 | 第一个参数传入 |
| 参数类型 | 任何可迭代对象（list, tuple, generator 等） | `Iterable<? extends CharSequence>` 或 `CharSequence[]` |
| 非字符串元素 | 报 `TypeError` | 编译报错（泛型约束） |
| 等效手写 | `s = ""; for x in list: s += x` | `StringBuilder sb = new StringBuilder(); for (String x : list) sb.append(x);` |

## 要点

1. **记法差异**：Python 的连接符写在**前面**（`"," .join(...)`），Java 的连接符写在**第一个参数**（`String.join(",", ...)`）
2. **性能**：Python 的 `join` 是 O(n) 且预分配内存，比 `+=` 拼串（O(n²)）快得多；Java 中 `String.join` 内部使用 `StringJoiner`/`StringBuilder`，也比 `+` 高效
3. **空字符串作为分隔符**：`"".join(list)` 纯拼接无分隔，等效于 Java 的 `String.join("", list)`
