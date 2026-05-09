# 链式调用与方法命名对比：Java vs Python

## 代码对比

```python
# Python: OpenAI SDK 的链式调用
response = self.client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "你好"}]
)
# 逐层拆解：
# self.client          -> OpenAI 客户端实例
#            .chat          -> 聊天命名空间
#                 .completions -> 补全资源
#                              .create()  -> 执行创建操作
```

```java
// Java 常见的几种等价写法：

// 1. 传统 Java 风格（层层 get）
OpenAIClient client = new OpenAIClient(apiKey);
ChatNamespace chat = client.getChat();
CompletionResource completions = chat.getCompletions();
CreateCompletionResponse response = completions.create(request);

// 2. Builder 模式（Java 常用）
OpenAIClient client = OpenAIClient.builder()
    .apiKey(apiKey)
    .build();
CreateCompletionRequest request = CreateCompletionRequest.builder()
    .model("gpt-4")
    .addMessage(Message.builder().role("user").content("你好").build())
    .build();
CreateCompletionResponse response = client.createCompletion(request);
```

## 差异表格

| 对比项 | Python OpenAI SDK | Java 风格 |
|--------|------------------|-----------|
| 调用链 | `client.chat.completions.create()` 连续点号 | 通常用 Builder 或层层 getter |
| 参数传法 | 关键字参数 `model="xxx"` | 请求对象 builder 构建 |
| 命名风格 | 全小写蛇形命名 | 驼峰命名 + getter/setter |
| 设计哲学 | 轻量、少写代码 | 类型安全、IDE 自动补全友好 |

## 为什么 Python SDK 这么设计

这是一种**分层命名空间**设计：

```
client              → 顶层客户端
 └── chat           → 聊天相关功能
      └── completions → 补全相关操作
           └── create() → 实际执行
```

每层负责缩小范围，最后 `create()` 才真正干活。好处是：

1. **IDE 自动补全友好** —— 敲 `client.chat.` 就只显示聊天相关的方法
2. **命名空间隔离** —— 不会和 `client.images`、`client.models` 等方法混在一起
3. **链式可读** —— 读代码时从右往左看：`create` 一个 `completions`，在 `chat` 里，通过 `client` 调用

## 要点说明

1. **这不是 Python 语法特性**，只是 OpenAI SDK 的 API 设计风格。Python 里方法可以返回 `self` 来实现链式调用，也可以像这样返回子模块对象
2. **Java 要做类似效果**更麻烦 —— 每个中间对象都要定义类型，不像 Python 那样动态无类型约束
3. **`.create()` 不叫 `createCompletion()`** 是因为已经在 `chat.completions` 命名空间下了，函数名不用重复上下文 —— 这也是一种 Pythonic 风格
