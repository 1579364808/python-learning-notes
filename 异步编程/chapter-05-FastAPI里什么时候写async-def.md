# 第 5 章：FastAPI 里什么时候写 `async def`

## 本章只解决一个问题

写 FastAPI 接口时，到底用 `def` 还是 `async def`？

## 先看代码

普通接口：

```python
@app.get("/ping")
def ping():
    return {"message": "pong"}
```

异步接口：

```python
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    user = await query_user_from_db(user_id)
    return user
```

## 你应该观察到什么

如果函数里没有 `await`，可以用普通 `def`：

```python
def ping():
    return {"message": "pong"}
```

如果函数里需要 `await`，必须用 `async def`：

```python
async def get_user(user_id: int):
    user = await query_user_from_db(user_id)
    return user
```

因为 Python 规定：`await` 只能出现在 `async def` 里面。

## 判断规则

### 情况 1：只是计算或返回固定数据

用 `def` 就行：

```python
@app.get("/add")
def add(a: int, b: int):
    return {"result": a + b}
```

### 情况 2：调用异步数据库、异步 HTTP、异步 Redis

用 `async def`：

```python
@app.get("/profile")
async def profile():
    user = await db.get_user()
    return user
```

### 情况 3：调用 `requests` 这种同步库

不要因为用了 FastAPI 就强行写 `async def`：

```python
@app.get("/bad")
async def bad():
    response = requests.get("https://example.com")  # 不推荐
    return response.json()
```

这会阻塞事件循环。

更简单的入门建议：如果你暂时只会用同步库，就先写普通 `def`。

```python
@app.get("/ok")
def ok():
    response = requests.get("https://example.com")
    return response.json()
```

## 用 Java 类比一句话

`async def` 不是"更高级的 def"，它更像声明：这个方法内部会用异步等待，框架要按异步方式调度它。

## 现在只需要记住

- 函数里要写 `await` -> 用 `async def`。
- 函数里没有 `await` -> 用 `def` 也可以。
- `async def` 里不要直接调用 `time.sleep()`、`requests.get()` 这类同步阻塞函数。
- FastAPI 支持 `def` 和 `async def`，不是所有接口都必须异步。

## 小练习

下面函数应该用 `def` 还是 `async def`？

```python
@app.get("/user")
??? get_user():
    user = await db.get_user()
    return user
```

答案：必须用 `async def`，因为函数体里有 `await`。
