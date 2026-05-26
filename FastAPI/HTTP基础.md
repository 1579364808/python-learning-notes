# HTTP 基础——Web 开发者必须知道的知识

## 一句话

HTTP 是浏览器（客户端）和服务器之间**对话的格式约定**。你发什么格式的请求，服务器返回什么格式的响应，都由 HTTP 协议规定。

---

## 1. 一个完整的 HTTP 请求长什么样

### 请求（Request）—— 浏览器发给服务器

```text
POST /api/users HTTP/1.1                      ← 请求行：方法 + 路径 + 协议版本
Host: example.com                              ← 请求头：键值对
Content-Type: application/json
Authorization: Bearer xyz123
User-Agent: Mozilla/5.0

{"name": "Alice", "age": 25}                   ← 请求体：实际数据（GET 没有体）
```

### 响应（Response）—— 服务器返回给浏览器

```text
HTTP/1.1 201 Created                           ← 状态行：协议版本 + 状态码 + 原因短语
Content-Type: application/json                 ← 响应头：键值对
Set-Cookie: session_id=abc123
Content-Length: 45

{"id": 1, "name": "Alice", "age": 25}          ← 响应体：实际数据
```

### 在 FastAPI 里，你不直接拼这些字符串

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class User(BaseModel):
    name: str
    age: int

@app.post("/api/users", status_code=201)          # ← 你只关心方法和路径
def create_user(user: User):                      # ← 框架自动解析请求体
    return {"id": 1, **user.model_dump()}          # ← 框架自动序列化响应体
```

但**理解报文结构**能帮你：
- 看浏览器 Network 面板时知道每列是什么意思
- 看 API 文档时知道该传什么、会收到什么
- 出现 4xx/5xx 时知道问题出在哪一端

---

## 2. HTTP 方法（动词）

| 方法 | 含义 | 类比 SQL | 幂等？ | 有请求体？ | FastAPI 写法 |
|------|------|---------|--------|-----------|-------------|
| **GET** | 获取资源 | SELECT | ✅ 是 | ❌ 无 | `@app.get()` |
| **POST** | 创建资源 | INSERT | ❌ 否 | ✅ 有 | `@app.post()` |
| **PUT** | 全量替换 | UPDATE（全量） | ✅ 是 | ✅ 有 | `@app.put()` |
| **PATCH** | 局部更新 | UPDATE（部分） | ❌ 否 | ✅ 有 | `@app.patch()` |
| **DELETE** | 删除资源 | DELETE | ✅ 是 | ❌ 一般无 | `@app.delete()` |

### 幂等是什么意思？

**幂等** = 同一个请求执行 1 次和执行 100 次，结果一样。

```text
GET /user/1          → 第 1 次返回 Alice，第 100 次还是 Alice  ✅ 幂等
DELETE /user/1       → 第 1 次删掉，第 100 次报 404，结果都是「没有 user 1」 ✅ 幂等
POST /user           → 第 1 次创建 Alice，第 100 次又创建一个 Alice ❌ 不幂等
```

**为什么你要知道？** 网络请求可能超时重发。`GET` 和 `PUT` 可以安全重试，`POST` 不能（会重复创建）。

### 什么时候用哪个？

| 场景 | 方法 | 路径 |
|------|------|------|
| 获取用户列表 | GET | `/users` |
| 获取单个用户 | GET | `/users/{id}` |
| 创建新用户 | POST | `/users` |
| 替换整个用户信息 | PUT | `/users/{id}` |
| 修改用户邮箱 | PATCH | `/users/{id}` |
| 删除用户 | DELETE | `/users/{id}` |

---

## 3. 状态码

服务器用状态码告诉浏览器「你的请求结果怎么样」。

### 分类

| 范围 | 类别 | 含义 |
|------|------|------|
| `1xx` | 信息 | 服务器收到了，还在处理（基本见不到） |
| **`2xx`** | **成功** | 请求正常处理了 |
| **`3xx`** | **重定向** | 你要的东西不在这，去别处找 |
| **`4xx`** | **客户端错误** | 你（客户端）发的东西有问题 |
| **`5xx`** | **服务器错误** | 我（服务器）挂了 |

### 常见的

| 状态码 | 英文 | 含义 | 你的代码该怎么做 |
|--------|------|------|----------------|
| **200** | OK | 成功了 | 正常处理返回数据 |
| **201** | Created | 创建成功 | POST 创建资源后返回 |
| **204** | No Content | 成功了但没数据 | DELETE 成功后用 |
| **301** | Moved Permanently | 永久重定向 | 网站换域名了 |
| **302** | Found | 临时重定向 | 登录后跳转 |
| **400** | Bad Request | 你发的请求格式不对 | 参数校验失败 |
| **401** | Unauthorized | 没登录 | 需要登录 |
| **403** | Forbidden | 没权限 | 登录了但不允许访问 |
| **404** | Not Found | 资源不存在 | 路径写错了或 ID 不存在 |
| **405** | Method Not Allowed | 方法不允许 | 路径对了但方法错（如 POST 写成了 GET） |
| **422** | Unprocessable Entity | 请求体格式不对 | FastAPI 数据校验失败时返回 |
| **429** | Too Many Requests | 请求太频繁 | 被限流了 |
| **500** | Internal Server Error | 服务器内部错误 | 你的代码抛异常了 |
| **502** | Bad Gateway | 上游服务器挂了 | Nginx 后面的服务没启动 |
| **503** | Service Unavailable | 服务暂时不可用 | 服务器过载或维护中 |

### 在 FastAPI 中

```python
@app.post("/users", status_code=201)          # 设置状态码
def create_user(user: User):
    return {"id": 1, **user.model_dump()}

# 或者动态返回
from fastapi import status
from fastapi.responses import JSONResponse

@app.post("/users")
def create_user(user: User):
    return JSONResponse(
        content={"id": 1, "name": user.name},
        status_code=status.HTTP_201_CREATED
    )
```

---

## 4. 常见的请求头

| 请求头 | 作用 | 例子 |
|--------|------|------|
| `Host` | 目标服务器域名（HTTP/1.1 必须） | `Host: example.com` |
| `Content-Type` | 请求体的格式 | `application/json` / `application/x-www-form-urlencoded` / `multipart/form-data` |
| `Authorization` | 身份认证信息 | `Bearer eyJxxx...` / `Basic base64(...)` |
| `Accept` | 客户端希望收到的格式 | `application/json` / `text/html` |
| `User-Agent` | 客户端标识 | `Mozilla/5.0 ...` / `curl/8.0` |
| `Cookie` | 浏览器保存的会话信息 | `session_id=abc123` |
| `Referer` | 请求来源页面 | `https://example.com/page1` |
| `Origin` | 请求来源域名（CORS 用） | `https://example.com` |

### 常见的响应头

| 响应头 | 作用 | 例子 |
|--------|------|------|
| `Content-Type` | 响应体的格式 | `application/json; charset=utf-8` |
| `Content-Length` | 响应体大小（字节） | `Content-Length: 45` |
| `Set-Cookie` | 让浏览器保存 cookie | `session_id=abc123; HttpOnly; Path=/` |
| `Cache-Control` | 缓存策略 | `no-cache` / `max-age=3600` |
| `Location` | 重定向目标 URL | `Location: /login`（配合 302） |
| `Access-Control-Allow-Origin` | CORS 跨域允许 | `*`（允许所有域名） |

---

## 5. RESTful API 设计——URL 怎么写

REST 不是标准，是**约定俗成的风格**，大多数 Web API 都用它。

### 核心原则

1. **用名词表示资源**，不用动词
2. **用 HTTP 方法表示操作**
3. **用层级结构表示关系**

```text
❌ 不好的设计：用动词
GET /getUser
POST /createUser
POST /deleteUser

✅ 好的设计：用名词 + HTTP 方法
GET    /users           → 获取用户列表
GET    /users/{id}      → 获取单个用户
POST   /users           → 创建用户
PUT    /users/{id}      → 替换用户
PATCH  /users/{id}      → 更新用户部分字段
DELETE /users/{id}      → 删除用户
```

### 资源关系怎么表达

```text
# 用户 123 的订单
GET /users/123/orders          → 用户 123 的所有订单
GET /users/123/orders/456      → 用户 123 的订单 456

# 过滤、排序、分页——用查询参数
GET /users?age=18              → 筛选年龄为 18 的用户
GET /users?page=1&size=20      → 分页
GET /users?sort=-created_at    → 按创建时间倒序
```

---

## 6. HTTP 是无状态的——那怎么保持登录？

**无状态** = 每次 HTTP 请求都是独立的，服务器不记得你之前来过。

```text
第 1 次请求： 浏览器 → GET /index.html                → 服务器返回首页
第 2 次请求： 浏览器 → GET /profile                   → 服务器：？？你是谁
```

那登录功能怎么实现的？三种主流方案：

### 方案 1：Cookie + Session（传统 Web）

```text
浏览器                         服务器
  │  POST /login                  │
  │  {"username":"alice"}         │
  │ ──────────────────────────→   │ 验证通过，创建 session
  │  Set-Cookie: session=abc123   │ 把 session id 写到 cookie
  │ ←──────────────────────────   │
  │                               │
  │  GET /profile                 │
  │  Cookie: session=abc123       │ 浏览器自动带上 cookie
  │ ──────────────────────────→   │ 查 session，知道是 alice
  │  {"name": "Alice"}            │
  │ ←──────────────────────────   │
```

### 方案 2：JWT Token（现代 API 常用）

```text
浏览器                         服务器
  │  POST /login                  │
  │  {"username":"alice"}         │
  │ ──────────────────────────→   │ 验证通过，签发 JWT token
  │  {"token": "eyJxxx..."}       │
  │ ←──────────────────────────   │
  │                               │
  │  GET /profile                 │
  │  Authorization: Bearer eyJ... │ 前端手动在 header 里带上 token
  │ ──────────────────────────→   │ 验证 token 签名，知道是 alice
  │  {"name": "Alice"}            │
  │ ←──────────────────────────   │
```

### 方案 3：API Key（机器间通信）

```text
客户端（另一个服务）              服务器
  │  GET /api/data                │
  │  X-API-Key: sk-xxxxxxxx       │ 每次请求都带 key
  │ ──────────────────────────→   │ 验证 key 是否有效
```

**区别：**

| | Cookie + Session | JWT | API Key |
|--|----------------|-----|---------|
| 状态存哪儿 | 服务器内存/数据库 | token 本身包含信息 | 服务器数据库 |
| 适合场景 | 传统 Web 网站 | 前后端分离、移动端 | 服务间调用 |
| FastAPI 实现 | `starlette.sessions` | `python-jose` / `PyJWT` | 自定义中间件 |

---

## 7. Content-Type——你发给服务器的数据格式

这是新手最容易搞混的东西。`Content-Type` 告诉服务器：**我发给你的数据是什么格式**。

### 常见的 Content-Type

| Content-Type | 请求体长这样 | 什么时候用 |
|-------------|-------------|-----------|
| `application/json` | `{"name": "Alice", "age": 25}` | **前后端分离的 API，最常用** |
| `application/x-www-form-urlencoded` | `name=Alice&age=25` | HTML 表单提交（传统） |
| `multipart/form-data` | `--boundary\r\nContent-Disposition: form-data; name="file"\r\n\r\n...` | **上传文件** |
| `text/plain` | 纯文本 | 很少用 |
| `application/octet-stream` | 二进制数据 | 下载文件 |

### 在 FastAPI 中

```python
# JSON（默认，最常用）
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int

@app.post("/users")
def create_user(user: User):                    # FastAPI 自动读 Content-Type: application/json
    return user

# 表单数据（传统 HTML 表单）
from fastapi import Form

@app.post("/login")
def login(username: str = Form(), password: str = Form()):   # FastAPI 自动读 form 数据
    return {"username": username}

# 文件上传
from fastapi import UploadFile, File

@app.post("/upload")
def upload(file: UploadFile = File()):          # FastAPI 自动读 multipart/form-data
    return {"filename": file.filename}
```

**简单记：只要你的前端用 `fetch` / `axios` 发 JSON，就是 `application/json`，FastAPI 用 Pydantic 模型接收。只要上传文件，就是 `multipart/form-data`。**

---

## 8. 从浏览器输入 URL 到页面显示——完整流程

```
你输入 https://example.com/users
    │
    ├── 1. DNS 解析：把域名 example.com 转成 IP 地址 93.184.216.34
    │
    ├── 2. TCP 连接：三次握手建立连接
    │
    ├── 3. TLS 握手：如果是 HTTPS，协商加密（就是 SSL/TLS）
    │
    ├── 4. 发送 HTTP 请求：
    │       GET /users HTTP/1.1
    │       Host: example.com
    │       Accept: text/html,application/json
    │       ...
    │
    ├── 5. 服务器处理请求（FastAPI 路由匹配、业务逻辑、查数据库）
    │
    ├── 6. 返回 HTTP 响应：
    │       HTTP/1.1 200 OK
    │       Content-Type: application/json
    │       [
    │         {"id": 1, "name": "Alice"},
    │         {"id": 2, "name": "Bob"}
    │       ]
    │
    └── 7. 浏览器解析响应，渲染页面（或 JS 处理数据）
```

作为后端开发者，你只需要关心 **4、5、6**。其他三步由浏览器、DNS、网络库自动完成。

---

## 9. HTTPS 和 HTTP 有什么区别？

| | HTTP | HTTPS |
|--|------|-------|
| 数据传输 | **明文**，可以被中间人偷看 | **加密**，WiFi 上的黑客也看不懂 |
| 默认端口 | 80 | 443 |
| 是否需要证书 | 不需要 | 需要 SSL/TLS 证书 |
| 是否信任 | 浏览器会标「不安全」 | 浏览器显示小锁🔒 |

**作为开发者**：生产环境必须用 HTTPS。开发环境（localhost）用 HTTP 就可以。FastAPI 部署时通常前面挂 Nginx/Caddy 处理 HTTPS，FastAPI 本身不直接处理。

---

## 10. 快速自测——这些你都能答上来吗？

1. GET 和 POST 的区别是什么？
2. 401 和 403 有什么区别？什么时候返回哪个？
3. 为什么 POST 创建资源返回 201，但很多项目用 200？—— 两种都对，但 201 更准确
4. 你的 API 返回的 Content-Type 是什么？—— FastAPI 默认 `application/json`
5. 什么是幂等？哪些 HTTP 方法是幂等的？
6. 用户登录后，后续请求怎么识别身份？—— Cookie/Session 或 JWT
7. POST 提交 JSON 和提交表单数据，请求头有什么区别？

---

## 参考

- [MDN: HTTP](https://developer.mozilla.org/zh-CN/docs/Web/HTTP) — 最权威的 HTTP 文档
- FastAPI 文档中关于请求和响应的部分
- 浏览器 F12 → Network 面板，看真实请求
