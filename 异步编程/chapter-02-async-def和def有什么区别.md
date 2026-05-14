# 第 2 章：`async def` 和 `def` 有什么区别

## 本章只解决一个问题

`def` 和 `async def` 都是定义函数，它们到底差在哪？

## 先看代码

普通函数：

```python
def hello():
    print("函数开始")
    return "Hello"


result = hello()
print(result)
```

输出：

```text
函数开始
Hello
```

异步函数：

```python
async def hello_async():
    print("函数开始")
    return "Hello"


result = hello_async()
print(result)
```

输出类似：

```text
<coroutine object hello_async at 0x...>
```

你会发现：`函数开始` 没有打印。

## 你应该观察到什么

普通函数：

```python
result = hello()
```

这句会立刻执行函数体。

异步函数：

```python
result = hello_async()
```

这句**不会立刻执行函数体**，只是得到一个协程对象。

要让它真正执行，需要交给 `asyncio.run()`：

```python
import asyncio


async def hello_async():
    print("函数开始")
    return "Hello"


result = asyncio.run(hello_async())
print(result)
```

输出：

```text
函数开始
Hello
```

## 用 Java 类比一句话

普通 `def` 像 Java 普通方法，调用就执行；`async def` 调用后更像先拿到一个"将来要执行的任务对象"，还没真正跑。

## 现在只需要记住

- `def hello()`：调用后马上执行。
- `async def hello()`：调用后先得到协程对象。
- 协程对象需要 `await` 或 `asyncio.run()` 才会真正执行。
- FastAPI 会帮你执行接口函数，所以接口里通常不用自己写 `asyncio.run()`。

## 小练习

判断下面哪一句会打印 `开始`：

```python
async def work():
    print("开始")


work()
```

答案：不会。这里只是创建了协程对象，没有执行它。
