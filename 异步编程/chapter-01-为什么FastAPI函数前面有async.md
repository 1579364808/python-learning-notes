# 第 1 章：为什么 FastAPI 函数前面有 `async`

## 本章只解决一个问题

为什么 FastAPI 示例代码经常这样写：

```python
@app.get("/")
async def root():
    return {"message": "Hello World"}
```

## 先看代码

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}
```

这里有两件事：

```python
@app.get("/")
```

这一行负责把 `/` 这个网址和下面的函数绑定起来。

```python
async def root():
```

这一行表示：`root` 是一个**异步函数**。

## 你应该观察到什么

FastAPI 收到浏览器请求 `/` 时，会调用 `root()`。

如果 `root()` 里面只是直接返回数据：

```python
async def root():
    return {"message": "Hello World"}
```

那它和普通函数看起来差不多。

但如果以后里面要等数据库、等网络请求：

```python
async def root():
    user = await get_user_from_db()
    return user
```

`async def` 就有用了：等待数据库时，FastAPI 可以先去处理别的请求。

## 用 Java 类比一句话

`async def` 有点像 Java 中"这个方法将来可能返回一个异步结果"，但 Python 用 `await` 把异步代码写得像普通顺序代码。

## 现在只需要记住

- `@app.get("/")`：注册接口地址。
- `async def root()`：定义一个异步接口函数。
- 如果函数里以后要用 `await`，外层就必须写 `async def`。
- 现在不用急着懂底层事件循环。

## 小练习

把下面代码读成中文：

```python
@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
```

参考答案：当访问 `/hello/张三` 时，FastAPI 调用 `say_hello`，把路径里的 `张三` 传给 `name`，最后返回 JSON。
