# 第 3 章：`await` 到底在等什么

## 本章只解决一个问题

`await` 是不是会把整个程序卡住？

## 先看代码

```python
import asyncio


async def work():
    print("开始")
    await asyncio.sleep(2)
    print("结束")


asyncio.run(work())
```

输出：

```text
开始
等待 2 秒
结束
```

这里的关键是：

```python
await asyncio.sleep(2)
```

意思不是"整个服务器睡 2 秒"，而是"当前这个任务等 2 秒，其他任务可以先跑"。

## 你应该观察到什么

`await` 只暂停**当前这个异步函数**。

比如有两个请求：

```python
async def request_a():
    await asyncio.sleep(2)
    return "A 完成"


async def request_b():
    return "B 完成"
```

当 `request_a` 在等 2 秒时，服务器可以先处理 `request_b`。

这就是 FastAPI 喜欢异步函数的原因：一个请求在等数据库时，不影响其他请求。

## 用 Java 类比一句话

Java 里 `future.get()` 通常会阻塞当前线程；Python 的 `await` 是"等结果，但把线程让出来给别人用"。

## 现在只需要记住

- `await` 后面跟的是一个异步操作。
- `await` 会暂停当前函数。
- `await` 不等于卡死整个服务器。
- `await` 只能写在 `async def` 里面。

## 小练习

下面代码为什么合法？

```python
async def root():
    data = await get_data()
    return data
```

答案：因为 `await` 写在 `async def` 里面。
