# 字符串插值对比：Java vs Python

## 代码对比

```python
# Python: f-string（格式化字符串）
model = "gpt-4"
print(f"🧠 正在调用 {model} 模型...")
# 输出: 🧠 正在调用 gpt-4 模型...

# 花括号里可以放任意表达式
print(f"2 + 3 = {2 + 3}")          # 2 + 3 = 5
print(f"名字: {user.name}")         # 访问属性
print(f"结果: {func()}")            # 调用函数
```

```java
// Java: 不同时代的写法

// 1. 字符串拼接（老式）
System.out.println("🧠 正在调用 " + model + " 模型...");

// 2. String.format（类似 C 的 printf）
System.out.println(String.format("🧠 正在调用 %s 模型...", model));

// 3. MessageFormat（复杂替换）
System.out.println(MessageFormat.format("🧠 正在调用 {0} 模型...", model));

// 4. Java 15+ STR."..."（文本块模板，预览功能）
// System.out.println(STR."🧠 正在调用 \{model\} 模型...");
```

## 差异表格

| 对比项 | Python `f"..."` | Java |
|--------|----------------|------|
| 语法 | `f"文本 {变量} 文本"` | `"文本 " + 变量 + " 文本"`（拼接） |
| 表达式 | 花括号里直接写任意代码：`{x + y}`、`{func()}` | 拼接才能写表达式 |
| 简洁度 | 最简洁，Python 3.6+ 引入 | 拼接最啰嗦，`String.format` 次之 |
| 花括号转义 | `{{` 输出 `{` | 不需要（拼接法）或 `%%`（format 法）|
| emoji 支持 | Python 3 原生支持 Unicode | Java 也支持，但拼接更乱 |

## 要点说明

1. **f-string = format string**，前面的 `f` 告诉 Python 这是个格式化字符串，花括号 `{}` 里的内容会被计算并替换
2. **花括号里可以是任意 Python 表达式**：变量、运算、函数调用、三元表达式都行
3. **Python 3.6 之前**只能用 `"xxx %s" % var` 或 `"{}".format(var)`，有了 f-string 后简洁太多了
4. **对比 Java**：最接近的是 Java 15 的 `STR."..."`（预览功能），但远不如 Python 的 f-string 成熟和普及
