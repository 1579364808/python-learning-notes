# 第 6 章：常见错误

## 本章只解决一个问题

刚学 `async/await` 时，最容易写错哪些地方？

## 错误 1：忘记 `await`

错误写法：

```python
async def get_user():
    return {"name": "Tom"}


async def root():
    user = get_user()
    return user
```

这里的 `user` 不是用户数据，而是协程对象。

正确写法：

```python
async def root():
    user = await get_user()
    return user
```

现在只记住：调用异步函数时，通常要 `await`。

## 错误 2：在 `async def` 里用 `time.sleep()`

错误写法：

```python
import time


async def root():
    time.sleep(3)
    return {"ok": True}
```

`time.sleep(3)` 会让当前线程真的睡 3 秒，可能卡住其他请求。

正确写法：

```python
import asyncio


async def root():
    await asyncio.sleep(3)
    return {"ok": True}
```

## 错误 3：在 `async def` 里直接用 `requests`

错误写法：

```python
import requests


async def root():
    response = requests.get("https://example.com")
    return response.json()
```

`requests.get()` 是同步阻塞的。

入门时有两个选择：

```python
# 选择 1：先写普通 def
def root():
    response = requests.get("https://example.com")
    return response.json()
```

```python
# 选择 2：换成异步 HTTP 库
import httpx


async def root():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://example.com")
    return response.json()
```

## 错误 4：以为 `await a(); await b()` 是并发

错误理解：

```python
user = await get_user()
orders = await get_orders()
```

这不是并发，是串行。

如果两个操作互不依赖，用：

```python
user, orders = await asyncio.gather(
    get_user(),
    get_orders(),
)
```

## 用 Java 类比一句话

这些错误本质上类似 Java 里把异步任务当普通结果用、或者在异步流程里偷偷写了阻塞调用。

## 现在只需要记住

- 调异步函数，通常要 `await`。
- `async def` 里别用 `time.sleep()`。
- `async def` 里别直接用 `requests`。
- 想并发等多个任务，用 `asyncio.gather()`。

## 小练习

找出这段代码的问题：

```python
@app.get("/demo")
async def demo():
    time.sleep(2)
    user = get_user()
    return user
```

答案：

- `time.sleep(2)` 会阻塞，应该改成 `await asyncio.sleep(2)`。
- `get_user()` 如果是异步函数，应该写 `await get_user()`。
