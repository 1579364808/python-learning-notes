# FastAPI 从零开始

---

## 第一课：认识 FastAPI — 最简单的 API

### 什么是 FastAPI？

FastAPI 是一个 Python Web 框架，特点：

- **快** — 性能对标 Node.js + Go
- **自动文档** — 访问 `/docs` 就有 Swagger UI
- **类型驱动** — 你用 Python 类型注解写代码，FastAPI 自动帮你校验、序列化、生成文档

### 最小化应用

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello World"}
```

这就是一个完整的 FastAPI 应用。运行方式：

```bash
pip install fastapi uvicorn
uvicorn app:app --reload    # app:app = 文件名:变量名
```

访问：
- `http://127.0.0.1:8000/` → `{"message": "Hello World"}`
- `http://127.0.0.1:8000/docs` → Swagger UI（自动生成！）
- `http://127.0.0.1:8000/openapi.json` → OpenAPI 规范文件

> `--reload` 是在开发模式下自动重启，改了代码不用手动重启服务器。

### Python 类型注解复习

FastAPI 的核心理念：**你写类型注解，FastAPI 做剩下的事**。

```python
@app.get("/items/{item_id}")
def read_item(item_id: int):    # ← 这个 int 就是关键
    return {"item_id": item_id}
```

访问 `/items/42` → `{"item_id": 42}`
访问 `/items/abc` → ❌ 自动返回 422，告诉你是无效的 int

### 和 Pydantic 的关系

回头看**最小的 Pydantic 用法**：

```python
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float

@app.post("/items")
def create_item(item: Item):     # ← FastAPI 自动用 Pydantic 校验请求体
    return item
```

> FastAPI **底层就是 Pydantic**。你写 `item: Item` 时，FastAPI 自动把请求体 JSON 传给 `Item(**json_data)` 做校验。校验通过 → 得到 `Item` 实例；失败 → 422 + 错误详情。

### 所有 HTTP 方法

```python
@app.get("/items")          # GET    — 查
@app.post("/items")         # POST   — 增
@app.put("/items/{id}")     # PUT    — 改（全量更新）
@app.patch("/items/{id}")   # PATCH  — 改（部分更新）
@app.delete("/items/{id}")  # DELETE — 删
```

---

**第一课结束。** 喊 **继续** 我开始第二课：路径参数、查询参数与 Pydantic 的结合。

---

## 第二课：路径参数与查询参数

### 路径参数 — 从 URL 路径中取值

路径参数是 URL 路径里**动态变化的部分**，用 `{ }` 声明：

```python
@app.get("/users/{user_id}")
def get_user(user_id: int):      # ← fastapi 自动把字符串转成 int
    return {"user_id": user_id}
```

| URL | 结果 |
|-----|------|
| `/users/42` | `{"user_id": 42}` |
| `/users/abc` | ❌ 422 — "abc" 不是有效 int |

**类型注解决定了路径参数的行为：**

```python
@app.get("/users/{user_id}")
def get_user(user_id: int):        # 自动转 int，自动校验
    ...

@app.get("/articles/{slug}")
def get_article(slug: str):        # 保留字符串，不做转换
    ...
```

> **规则：** `{user_id}` → 函数参数名必须匹配 `user_id`。参数名和路径变量名**完全一致**。

### 查询参数 — URL 中 ? 后面的部分

```python
@app.get("/items")
def list_items(skip: int = 0, limit: int = 10):
    return {"skip": skip, "limit": limit}
```

| URL | 结果 |
|-----|------|
| `/items` | `{"skip": 0, "limit": 10}`（用了默认值） |
| `/items?skip=20&limit=5` | `{"skip": 20, "limit": 5}` |
| `/items?skip=abc` | ❌ 422 — "abc" 不是 int |

**区分路径参数和查询参数：**

```python
@app.get("/users/{user_id}/articles")
def list_user_articles(
    user_id: int,               # ← 路径参数（从 URL 路径来）
    skip: int = 0,              # ← 查询参数（从 ? 后面来，有默认值）
    limit: int = 10,            # ← 查询参数
):
    ...
```

FastAPI 的规则很简单：

| 参数特征 | 来源 | 示例 |
|---------|------|------|
| 在路径 `{}` 中 | 路径参数 | `/users/{user_id}` |
| 不在路径中，**有默认值** | 查询参数 | `skip: int = 0` |
| 不在路径中，**是 Pydantic 模型** | 请求体 | `item: Item` |

> 一目了然——看函数签名就知道数据从哪来。

### 可选查询参数

```python
@app.get("/items")
def list_items(q: str | None = None):    # q 可传可不传
    if q:
        return {"q": q}
    return {"q": "没有传"}
```

| URL | 结果 |
|-----|------|
| `/items` | `{"q": "没有传"}` |
| `/items?q=hello` | `{"q": "hello"}` |

> `str | None = None` 表示"可以是字符串，也可以是 None，默认是 None"。

### 布尔类型查询参数

```python
@app.get("/items")
def list_items(completed: bool = False):
    return {"completed": completed}
```

| URL | 结果 |
|-----|------|
| `/items?completed=1` | `true` |
| `/items?completed=true` | `true` |
| `/items?completed=yes` | `true` |

> FastAPI 对 bool 很智能——`1/true/yes/on` 都算 `True`，`0/false/no/off` 都算 `False`。

### 路径参数 + 查询参数 + 请求体 混用

```python
from pydantic import BaseModel

class ArticleCreate(BaseModel):
    title: str
    content: str

@app.post("/users/{user_id}/articles")
def create_article(
    user_id: int,                  # 路径参数
    article: ArticleCreate,        # 请求体（Pydantic）
    publish: bool = True,          # 查询参数
):
    return {
        "user_id": user_id,
        "title": article.title,
        "publish": publish,
    }
```

> 三种数据来源写在一起，FastAPI 自动区分，彼此独立校验。这是 FastAPI 最核心的体验。

### 和 SQLAlchemy 的关联

有了路径参数和查询参数，就可以写**真正的查询**了：

```python
@app.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"error": "not found"}, 404
    return {"id": user.id, "name": user.name}
```

> 这就是所有 Web API 的基础：**URL → 参数 → 查数据库 → 返回 JSON**。

---

**第二课结束。** 喊 **继续** 我开始第三课：请求体与 Pydantic 的深度结合。

---

## 第三课：请求体与 Pydantic 深度结合

### 你已经会了基础

在 Pydantic 笔记中你已经学过：

```python
from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    email: str
    password: str = Field(min_length=6)

@app.post("/users")
def create_user(user: UserCreate):   # ← 请求体自动校验
    return user.model_dump()
```

这一课重点讲 FastAPI 专有的部分：**`response_model`**、**`status_code`**、**请求体高级技巧**。

### response_model — 自动过滤输出字段

```python
from pydantic import BaseModel

class UserCreate(BaseModel):
    name: str
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    # 注意：没有 password！

@app.post("/users", response_model=UserResponse)   # ← 关键！
def create_user(user: UserCreate):
    db_user = User(name=user.name, hashed_password=hash(user.password))
    # 假设 db_user 是 SQLAlchemy 对象
    return db_user
```

**`response_model` 做了什么？**

1. 路由函数 return 之后，FastAPI 用 `UserResponse.model_validate(return_value)` 过滤
2. `UserResponse` 里有的字段 → 保留并返回
3. `UserResponse` 里没有的字段 → **自动剔除**（比如 password）

> 对比：不用 `response_model` 时，你 return 什么前端就收到什么。**用了 `response_model`，输出格式由 Pydantic 模型保证。**

### 不加 model_config 也能用 response_model

```python
class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    # 没有 from_attributes=True 时，不能直接传 ORM 对象

# 方案 A：手动转 dict
@app.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(name=user.name, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"id": db_user.id, "name": db_user.name, "email": db_user.email}
    # ↑ 返回 dict，status_code 不涉及 from_attributes

# 方案 B：配合 from_attributes
class UserResponse(BaseModel):
    model_config = {"from_attributes": True}  # 允许从 ORM 映射
    id: int
    name: str
    email: str

@app.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(name=user.name, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user   # ← 直接返回 ORM 对象，response_model 自动映射
```

> **最佳实践：响应体模型都加上 `from_attributes=True`**，这样路由里既可以 return dict 也可以 return ORM 对象，灵活度最高。

### response_model 的过滤效果

```python
class UserDB(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    name: str
    email: str
    hashed_password: str

class UserPublic(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    name: str
    email: str

# GET /users/1 用 UserPublic → 没有 hashed_password
@app.get("/users/{user_id}", response_model=UserPublic)
def get_user(user_id: int, db: Session = Depends(get_db)):
    return db.query(User).filter(User.id == user_id).first()
```

这就是**"一个接口一个输出模型"**——不同接口看到不同字段，每个 Pydantic 模型定义一种"视图"。

### status_code — 控制 HTTP 状态码

```python
@app.post("/users", response_model=UserResponse, status_code=201)
def create_user(...):
    ...

@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(...):
    ...
```

| 状态码 | 含义 | 什么时候用 |
|--------|------|-----------|
| 200 | OK | GET 默认 |
| 201 | Created | POST 创建成功后 |
| 204 | No Content | DELETE 成功后 |
| 404 | Not Found | 资源不存在 |

> `status_code` 只是设置了成功时的状态码。错误状态码（404、422 等）由异常处理机制控制，和这个参数无关。

### status_code 配合 response_model 的完整示例

```python
@app.post("/users", response_model=UserResponse, status_code=201)
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    exists = db.query(User).filter(User.email == user_data.email).first()
    if exists:
        raise HTTPException(status_code=409, detail="邮箱已被注册")  # 409 Conflict

    db_user = User(name=user_data.name, email=user_data.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user

@app.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    db.delete(user)
    db.commit()
    return  # 204 不需要返回体
```

### 请求体嵌套

```python
class Tag(BaseModel):
    name: str
    color: str = "blue"

class ArticleCreate(BaseModel):
    title: str
    content: str
    tags: list[Tag] = []         # ← 请求体里嵌套列表

@app.post("/articles", response_model=ArticleResponse, status_code=201)
def create_article(article: ArticleCreate, db: Session = Depends(get_db)):
    ...
```

前端传：

```json
{
    "title": "FastAPI 入门",
    "content": "...",
    "tags": [
        {"name": "Python", "color": "green"},
        {"name": "API", "color": "red"}
    ]
}
```

**嵌套模型的好处：** JSON 结构有多深，Pydantic 就能校验多深。每个嵌套层级都独立校验——缺字段、类型不对，同样返回 422。

### response_model 的继承

随着接口增多，你会发现很多响应模型共享一些字段：

```python
class BaseResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    created_at: datetime = None

class UserResponse(BaseResponse):    # 继承了 id 和 created_at
    name: str
    email: str

class ArticleResponse(BaseResponse): # 继承了 id 和 created_at
    title: str
    content: str
    user_id: int
```

> 和 Pydantic 笔记里的三层架构一脉相承：**继承减少重复**，每个模型管好自己的那部分字段。

---

**第三课结束。** 喊 **继续** 我开始第四课：Path & Query 参数校验（`Path()`、`Query()`、`Depends()` 复用）。

---

## 第四课：Path、Query 参数校验与 Depends 依赖注入

### 上一课缺失的问题

第二课中，查询参数是这么写的：

```python
@app.get("/items")
def list_items(skip: int = 0, limit: int = 10):
    ...
```

如果我想限制 `limit` 最大 100，或者给参数加个描述呢？光靠 Python 类型注解做不到。

### Query() — 给查询参数加规则

```python
from fastapi import FastAPI, Query

@app.get("/items")
def list_items(
    q: str | None = Query(default=None, max_length=50),   # 最大 50 字符
    page: int = Query(default=1, ge=1),                    # ≥ 1
    page_size: int = Query(default=10, ge=1, le=100),      # 1~100
):
    return {"q": q, "page": page, "page_size": page_size}
```

`Query()` 参数速查：

| 参数 | 作用 | 示例 |
|------|------|------|
| `default` | 默认值 | `Query(default=None)` |
| `min_length` / `max_length` | 字符串长度 | `Query(default="", max_length=50)` |
| `ge` / `le` | 数值大小 | `Query(default=1, ge=1)` |
| `pattern` | 正则 | `Query(default=None, pattern=r"^\d{11}$")` |
| `description` | API 文档说明 | `Query(description="搜索关键词")` |
| `alias` | 参数别名 | `Query(alias="page-size")` |
| `deprecated` | 标记为废弃 | `Query(deprecated=True)` |

**非法数据的表现：**

| URL | 结果 |
|-----|------|
| `/items?page=0` | ❌ 422 — ge=1 |
| `/items?page_size=200` | ❌ 422 — le=100 |
| `/items?q=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa` | ❌ 422 — max_length=50 |

> 错误消息自动告诉用户违反了哪个规则，不用你自己写任何校验代码。

### Path() — 给路径参数加规则

```python
from fastapi import FastAPI, Path

@app.get("/users/{user_id}")
def get_user(
    user_id: int = Path(ge=1, description="用户 ID"),
):
    ...
```

`Path()` 和 `Query()` 的参数完全一样，只是作用的来源不同——一个管路径，一个管查询字符串。

### Query 和 Path 的区别

```python
@app.get("/users/{user_id}/articles/{article_id}")
def get_article(
    user_id: int = Path(ge=1),                    # 来自 URL 路径
    article_id: int = Path(ge=1),                  # 来自 URL 路径
    include_comments: bool = Query(default=False), # 来自 ? 后面
):
    ...
```

| 来源 | 写法 | 校验方式 |
|------|------|---------|
| 路径参数 | `user_id: int` 或 `user_id: int = Path(ge=1)` | `Path()` |
| 查询参数 | `q: str = Query(default=None)` 或 `q: str \| None = None` | `Query()` |

> 你甚至可以省略 `Path()`——单纯写 `user_id: int` 就够了。`Path()` 只在你需要加额外校验（ge、description）时才用。

### Depends() — 复用逻辑

如果多个接口都要"分页"，你可以在每个路由里写一遍 `page: int = Query(ge=1)`……但那是重复。**Depends 专治重复。**

```python
from fastapi import Depends

# 定义一次
def pagination(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
):
    return {"page": page, "page_size": page_size}

# 到处复用
@app.get("/users")
def list_users(pg: dict = Depends(pagination)):
    return pg

@app.get("/articles")
def list_articles(pg: dict = Depends(pagination)):
    return pg
```

> `Depends(pagination)` 的意思是：**"调用路由之前，先调用 `pagination()` 函数，把结果注入到路由参数里"**。

### Depends 返回 Pydantic 模型

上面返回 dict 类型不安全，配合 Pydantic 更好：

```python
from pydantic import BaseModel, Field

class Pagination(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)

    @property
    def offset(self) -> int:       # SQL 分页用
        return (self.page - 1) * self.page_size

# Depends 函数返回 Pydantic 实例
def get_pagination(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
) -> Pagination:
    return Pagination(page=page, page_size=page_size)

@app.get("/users")
def list_users(pg: Pagination = Depends(get_pagination), db: Session = Depends(get_db)):
    users = db.query(User).offset(pg.offset).limit(pg.page_size).all()
    return users
```

### 另一种写法：Pydantic 模型直接当 Depends

更简洁的方式——Pydantic 模型直接用 `Depends()`：

```python
class Pagination(BaseModel):
    model_config = {"extra": "forbid"}
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

@app.get("/users")
def list_users(pg: Pagination = Depends()):    # ← Depends() 不加参数
    return pg
```

请求 `GET /users?page=2&page_size=20`，FastAPI 自动从查询字符串创建 `Pagination` 实例。

> `Depends()` 不加参数时，FastAPI 自动把后面的类型（`Pagination`）当作依赖，从查询参数解析。

### 多个 Depends 叠加

```python
class Pagination(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)

class ArticleFilter(BaseModel):
    keyword: str = ""
    category_id: int | None = None

@app.get("/articles")
def list_articles(
    pg: Pagination = Depends(),
    flt: ArticleFilter = Depends(),
    db: Session = Depends(get_db),
):
    query = db.query(Article)
    if flt.keyword:
        query = query.filter(Article.title.contains(flt.keyword))
    total = query.count()
    items = query.offset(pg.offset).limit(pg.page_size).all()
    return {"total": total, "items": items, "page": pg.page}
```

URL: `GET /articles?page=1&page_size=10&keyword=python&category_id=2`

### Depends 用于数据库 Session

这是最常见的依赖——获取数据库会话：

```python
# database.py
from sqlalchemy.orm import Session

def get_db():
    db = SessionLocal()
    try:
        yield db         # ← 用 yield，FastAPI 会帮你在请求结束后关闭
    finally:
        db.close()

# router.py
@app.get("/users")
def list_users(db: Session = Depends(get_db)):   # 每个请求拿一个新的 Session
    return db.query(User).all()
```

`yield` 的作用：**请求处理前拿到 `db`，请求结束后自动执行 `finally` 关闭 `db`。**

### Depends 的传递

Depends 可以一层套一层，形成依赖链：

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(db: Session = Depends(get_db)) -> User:
    # 从 token 或 session 获取当前用户
    user = db.query(User).filter(User.id == 1).first()
    if not user:
        raise HTTPException(401, "未登录")
    return user

@app.get("/me")
def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user
```

> FastAPI 会自动解析依赖链：`get_current_user` 需要 `db` → FastAPI 先调 `get_db` 拿到 Session → 再调 `get_current_user`。

### 查询参数 vs Pydantic 模型 vs Depends — 怎么选？

| 情况          | 推荐写法                          |
| ----------- | ----------------------------- |
| 1-2 个简单查询参数 | 直接 `q: str \| None = None`    |
| 3+ 个查询参数    | 封装成 Pydantic 模型 + `Depends()` |
| 需要在多处复用     | 封装成 Pydantic 模型 + `Depends()` |
| 需要数据库或业务逻辑  | `def` 函数 + `Depends()`        |
| 需要获取当前用户    | `def` 函数 + `Depends()`        |

---

**第四课结束。** 喊 **继续** 我开始第五课：SQLAlchemy 集成配置与完整的 CRUD 路由。

---

## 第五课：SQLAlchemy 集成 — 从数据库连接到完整 CRUD

### 项目分层

```
project/
├── main.py         # FastAPI 入口
├── database.py     # 数据库连接
├── models.py       # SQLAlchemy 模型
└── schemas.py      # Pydantic 模型
```

### 1. database.py — 数据库连接

SQLAlchemy 2.0 标准写法：

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

SQLALCHEMY_DATABASE_URL = "sqlite:///./blog.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}   # SQLite 多线程支持
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db        # ← 请求中提供 Session
    finally:
        db.close()      # ← 请求结束自动关闭
```

### 2. models.py — SQLAlchemy 模型

```python
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(unique=True)
    hashed_password: Mapped[str]

    articles: Mapped[list["Article"]] = relationship(back_populates="author")

class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(Text)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    author: Mapped["User"] = relationship(back_populates="articles")
```

### 3. schemas.py — Pydantic 模型

```python
from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    model_config = {"extra": "forbid", "str_strip_whitespace": True}
    name: str = Field(min_length=2, max_length=50)
    email: str
    password: str = Field(min_length=6)

class ArticleCreate(BaseModel):
    model_config = {"extra": "forbid"}
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)

class ArticleResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    title: str
    content: str
    user_id: int

class UserResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    name: str
    email: str

class UserWithArticles(UserResponse):
    articles: list[ArticleResponse] = []

class Pagination(BaseModel):
    model_config = {"extra": "forbid"}
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size
```

### 4. main.py — 完整 CRUD

```python
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from hashlib import sha256

from database import engine, Base, get_db
from models import User, Article
from schemas import *

app = FastAPI()

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

# ==================== 用户 CRUD ====================

@app.post("/users", response_model=UserResponse, status_code=201)
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    exists = db.query(User).filter(User.email == user_data.email).first()
    if exists:
        raise HTTPException(409, "邮箱已注册")

    db_user = User(
        name=user_data.name,
        email=user_data.email,
        hashed_password=sha256(user_data.password.encode()).hexdigest(),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.get("/users", response_model=list[UserResponse])
def list_users(pg: Pagination = Depends(), db: Session = Depends(get_db)):
    users = db.query(User).offset(pg.offset).limit(pg.page_size).all()
    return users


@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "用户不存在")
    return user


@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_data: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "用户不存在")
    user.name = user_data.name
    user.email = user_data.email
    user.hashed_password = sha256(user_data.password.encode()).hexdigest()
    db.commit()
    db.refresh(user)
    return user


@app.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "用户不存在")
    db.delete(user)
    db.commit()
    return


# ==================== 文章 CRUD ====================

@app.post("/users/{user_id}/articles", response_model=ArticleResponse, status_code=201)
def create_article(user_id: int, article_data: ArticleCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "用户不存在")
    db_article = Article(title=article_data.title, content=article_data.content, user_id=user_id)
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    return db_article


@app.get("/articles", response_model=list[ArticleResponse])
def list_articles(pg: Pagination = Depends(), db: Session = Depends(get_db)):
    articles = db.query(Article).offset(pg.offset).limit(pg.page_size).all()
    return articles


@app.get("/users/{user_id}", response_model=UserWithArticles)
def get_user_with_articles(user_id: int, db: Session = Depends(get_db)):
    from sqlalchemy.orm import selectinload
    user = db.query(User).options(selectinload(User.articles)).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "用户不存在")
    return user
```

### 关键模式：三步曲

每个 CRUD 接口都遵循这个模式：

```
1. 参数校验 → FastAPI + Pydantic（自动完成）
2. 业务逻辑 → 手动查库、判断、操作
3. 返回结果 → response_model 自动过滤
```

> 这就是 FastAPI + Pydantic + SQLAlchemy 最标准的分层结构。大多数项目都从这个模板起步。

---

**第五课结束。** 喊 **继续** 我开始第六课：错误处理与 HTTPException 进阶。

---

## 第六课：错误处理 — HTTPException 与异常处理器

### 你已经会用 HTTPException

前面几课已经用过了：

```python
raise HTTPException(404, "用户不存在")
raise HTTPException(409, "邮箱已注册")
raise HTTPException(401, "未登录")
```

### HTTPException 的参数

```python
from fastapi import HTTPException

raise HTTPException(
    status_code=404,
    detail="用户不存在",           # 错误详情（str 或 dict）
    headers={"X-Error": "missing"}  # 自定义响应头（可选）
)
```

返回的 JSON：

```json
{
    "detail": "用户不存在"
}
```

> FastAPI 默认的异常响应格式就是 `{"detail": ...}`。这是规范，前端可以统一解析。

### 常见状态码

```python
HTTPException(400, "请求参数错误")     # Bad Request
HTTPException(401, "未登录")           # Unauthorized
HTTPException(403, "无权限")           # Forbidden
HTTPException(404, "资源不存在")        # Not Found
HTTPException(409, "数据冲突")          # Conflict
HTTPException(422, "校验失败")          # Unprocessable Entity（Pydantic 校验失败默认这个）
HTTPException(429, "请求太频繁")        # Too Many Requests
HTTPException(500, "服务器内部错误")    # Internal Server Error
```

### 什么时候用哪个？

| 场景 | 状态码 | 说明 |
|------|--------|------|
| 查询的资源不存在 | 404 | `if not user: raise HTTPException(404)` |
| 创建时数据已存在 | 409 | 邮箱已注册、用户名已存在 |
| 权限不足 | 403 | 不是自己的文章不能删 |
| 未登录 | 401 | 需要 token |
| 参数非法 | 422 | Pydantic 自动返回，你一般不用手动抛 |
| 业务条件不满足 | 400 | 余额不足、库存不够 |

### detail 可以是 dict

当你想返回更结构化的错误信息时，`detail` 可以传 dict：

```python
raise HTTPException(
    status_code=400,
    detail={
        "field": "email",
        "message": "该邮箱已被注册",
        "code": "EMAIL_EXISTS",
    }
)
```

返回：

```json
{
    "detail": {
        "field": "email",
        "message": "该邮箱已被注册",
        "code": "EMAIL_EXISTS"
    }
}
```

> 前端可以根据 `code` 字段做国际化或特定处理，比纯字符串更灵活。

### 全局异常处理器

如果你想让所有 404 返回统一的格式，或者想记录日志，用 `@app.exception_handler`：

```python
from fastapi import Request
from fastapi.responses import JSONResponse

# 捕获所有 HTTPException
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # 在这里可以加日志
    print(f"HTTP {exc.status_code}: {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": exc.detail,
            "success": False,
        },
    )
```

之前返回 `{"detail": "用户不存在"}`，现在返回：

```json
{
    "code": 404,
    "message": "用户不存在",
    "success": false
}
```

> 这样前端就有一套**统一格式的错误响应**，不需要每个接口单独处理。

### 捕获所有未处理的异常

```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # 记录日志
    print(f"未处理的异常: {exc}")
    # 生产环境不要暴露 exc 详情给前端
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误"},
    )
```

> **安全原则：** 全局兜底不要返回真实异常信息，防止信息泄露。

### 自定义异常类

如果你想：校验失败返回 `422` 和数据不存在返回 `404` 走不同的格式。先定义一个基类：

```python
class AppError(Exception):
    def __init__(self, message: str, code: int = 400):
        self.message = message
        self.code = code

class NotFoundError(AppError):
    def __init__(self, message: str = "资源不存在"):
        super().__init__(message, 404)

class AuthError(AppError):
    def __init__(self, message: str = "未登录"):
        super().__init__(message, 401)

# 注册处理器
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.code,
        content={"detail": exc.message},
    )

# 然后在路由里直接用
@app.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundError("用户不存在")      # ← 比 HTTPException 更简洁
    return user
```

### 验证错误的自定义处理

Pydantic 校验失败默认返回 422，格式是 `{"detail": [{"loc": [...], "msg": "...", "type": "..."}]}`。你可以自定义：

```python
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        errors.append({
            "field": ".".join(str(x) for x in err["loc"]),
            "message": err["msg"],
        })
    return JSONResponse(
        status_code=422,
        content={"code": 422, "errors": errors, "success": False},
    )
```

之前返回：

```json
{"detail": [{"loc": ["body", "age"], "msg": "Input should be greater than or equal to 1", "type": "greater_than_equal"}]}
```

现在返回：

```json
{
    "code": 422,
    "errors": [{"field": "body.age", "message": "Input should be greater than or equal to 1"}],
    "success": false
}
```

> 前端只需要关注 `errors` 列表，不用解析 Pydantic 原始格式。

### 异常处理优先级

```
自定义 @app.exception_handler(MyError)   ← 最高优先级
         ↓
@app.exception_handler(HTTPException)     ← 中间
         ↓
@app.exception_handler(Exception)          ← 全局兜底
```

FastAPI 按**最匹配**规则选择处理器。你的自定义异常类会被 `AppError` 的处理器捕获，不会被 `HTTPException` 抢走。

### 最佳实践总结

```python
# 1. 简单的 CRUD → 直接用 HTTPException
raise HTTPException(404, "用户不存在")

# 2. 统一格式 → 注册 exception_handler 改写响应结构
@app.exception_handler(HTTPException)
async def handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.detail},
    )

# 3. 大型项目 → 自定义异常类 + 异常处理器
```

---

**第六课结束。** 喊 **继续** 我开始第七课：中间件、CORS 与跨域问题。

---

## 第七课：中间件、CORS 与静态文件

### 什么是中间件？

中间件是**在每个请求处理前后执行的钩子**：

```
请求 → 中间件 → 路由函数 → 中间件 → 响应
         ↓                      ↑
      可以修改请求              可以修改响应
```

最常见的场景：

- CORS 跨域（前后端分离必备）
- 请求日志
- 响应时间统计
- 统一的请求头处理

### CORS — 跨域资源共享

**前后端分离的项目**（前端 3000 端口，后端 8000 端口），前端发请求会被浏览器拦截：

```
前端 http://localhost:3000  → 请求 → 后端 http://localhost:8000
                               ❌ 被浏览器拦截（跨域）
```

解决方法：后端告诉浏览器"我允许这个来源访问"。

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 允许所有来源（开发用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],               # 允许的域名
    allow_credentials=True,
    allow_methods=["*"],               # 允许的 HTTP 方法
    allow_headers=["*"],               # 允许的请求头
)
```

**生产环境**要指定具体的域名：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",        # 本地开发
        "https://myfrontend.com",       # 线上前端
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

> `allow_origins=["*"]` 和 `allow_credentials=True` **不能同时用**——浏览器安全策略。生产环境必须明确列出域名。

### 自定义中间件 — 统计响应时间

```python
import time
from fastapi import Request

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.time()
    response = await call_next(request)      # 执行路由函数
    process_time = time.time() - start
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

每次请求的响应头里会多一个 `X-Process-Time: 0.012`，方便排查慢接口。

### 自定义中间件 — 请求日志

```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"→ {request.method} {request.url.path}")
    response = await call_next(request)
    print(f"← {response.status_code}")
    return response
```

输出：

```
→ GET /users/1
← 200
→ POST /articles
← 201
```

### 中间件的执行顺序

```python
app.add_middleware(CORSMiddleware, ...)     # 1. 先注册
app.add_middleware(GzipMiddleware, ...)     # 2. 后注册
```

执行顺序：**后注册的先执行**（像洋葱，一层包一层）：

```
GzipMiddleware → CORSMiddleware → 路由 → CORSMiddleware → GzipMiddleware
```

### 静态文件 — 让 FastAPI 托管图片/文件

如果你的前端是直接由后端托管的，或者需要上传/下载文件：

```python
from fastapi.staticfiles import StaticFiles

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")
```

访问 `http://127.0.0.1:8000/static/logo.png` 就能拿到 `static/logo.png` 文件。

> `app.mount()` 会把整个路径交给另一个 ASGI 应用处理。除了静态文件，也可以挂载其他 WSGI/ASGI 应用。

### 文件上传

```python
from fastapi import UploadFile, File

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()           # 读取文件内容
    return {
        "filename": file.filename,        # 原始文件名
        "content_type": file.content_type, # MIME 类型
        "size": len(content),
    }
```

配合静态文件目录保存：

```python
import aiofiles

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    save_path = f"static/{file.filename}"
    async with aiofiles.open(save_path, "wb") as f:
        await f.write(await file.read())
    return {"url": f"/static/{file.filename}"}
```

---

**第七课结束。** 喊 **继续** 我开始第八课：Router 路由拆分 —— 告别单文件大杂烩。

---

## 第八课：APIRouter — 路由拆分

### 问题：一个文件写不下

第五课中所有路由都在 `main.py`：

```
main.py
├── POST /users
├── GET /users
├── GET /users/{id}
├── PUT /users/{id}
├── DELETE /users/{id}
├── POST /users/{id}/articles
├── GET /articles
└── GET /users/{id}
```

3 个模型 → 8 个路由 → 200 行。如果再加评论、分类、标签呢？一个文件会膨胀到上千行。

### 解决方案：APIRouter

`APIRouter` 就像"迷你 FastAPI 应用"，有自己的一组路由，最后注册到主应用。

### 项目结构

```
project/
├── main.py              # 主应用（注册所有 router）
├── database.py          # 数据库连接
├── models.py            # SQLAlchemy 模型
├── schemas.py           # Pydantic 模型
├── routers/
│   ├── __init__.py
│   ├── users.py         # 用户路由
│   └── articles.py      # 文章路由
```

### routers/users.py

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from hashlib import sha256

from database import get_db
from models import User
from schemas import UserCreate, UserResponse, UserWithArticles, Pagination

router = APIRouter(prefix="/users", tags=["用户"])   # ← 定义 router

@router.post("", response_model=UserResponse, status_code=201)
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    exists = db.query(User).filter(User.email == user_data.email).first()
    if exists:
        raise HTTPException(409, "邮箱已注册")
    db_user = User(
        name=user_data.name,
        email=user_data.email,
        hashed_password=sha256(user_data.password.encode()).hexdigest(),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("", response_model=list[UserResponse])
def list_users(pg: Pagination = Depends(), db: Session = Depends(get_db)):
    return db.query(User).offset(pg.offset).limit(pg.page_size).all()

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "用户不存在")
    return user

@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_data: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "用户不存在")
    user.name = user_data.name
    user.email = user_data.email
    user.hashed_password = sha256(user_data.password.encode()).hexdigest()
    db.commit()
    db.refresh(user)
    return user

@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "用户不存在")
    db.delete(user)
    db.commit()
```

> `prefix="/users"` 让 router 里所有路由自动加上 `/users` 前缀。`tags=["用户"]` 让 Swagger 文档分组显示。

### routers/articles.py

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from database import get_db
from models import Article, User
from schemas import ArticleCreate, ArticleResponse, Pagination

router = APIRouter(prefix="/users", tags=["文章"])

@router.post("/{user_id}/articles", response_model=ArticleResponse, status_code=201)
def create_article(user_id: int, article_data: ArticleCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "用户不存在")
    db_article = Article(title=article_data.title, content=article_data.content, user_id=user_id)
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    return db_article

# 独立文章路由
router_articles = APIRouter(prefix="/articles", tags=["文章"])

@router_articles.get("", response_model=list[ArticleResponse])
def list_articles(pg: Pagination = Depends(), db: Session = Depends(get_db)):
    return db.query(Article).offset(pg.offset).limit(pg.page_size).all()
```

> 一个文件可以有多个 `APIRouter` 实例，分别注册不同的前缀。

### main.py — 汇总

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from routers.users import router as users_router
from routers.articles import router as user_articles_router
from routers.articles import router_articles as articles_router

app = FastAPI()

# CORS
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# 建表
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

# 注册路由
app.include_router(users_router)
app.include_router(user_articles_router)
app.include_router(articles_router)
```

> `include_router` 之后，`users_router` 里所有路由自动带上 `/users` 前缀。

### 最终的路由表

```
POST    /users                  → users.py
GET     /users                  → users.py
GET     /users/{user_id}        → users.py
PUT     /users/{user_id}        → users.py
DELETE  /users/{user_id}        → users.py
POST    /users/{user_id}/articles → articles.py
GET     /articles               → articles.py
```

Swagger 文档里会自动分成 **"用户"** 和 **"文章"** 两个分组。

### APIRouter 的 prefix 如何工作

```python
router = APIRouter(prefix="/users")

@router.get("")          # 实际路径: /users
@router.get("/{id}")     # 实际路径: /users/{id}
@router.post("")         # 实际路径: /users
```

> `prefix` + `@router.get("")` = `/users`。路径拼接规则：**prefix 和路由路径用 `/` 拼接**，避免双斜杠。

### tags 的作用

```python
router = APIRouter(tags=["用户"])
router = APIRouter(tags=["文章"])
```

Swagger UI 上的效果：

```
┌─ 用户 ─────────────────┐
│ POST /users             │
│ GET /users              │
│ GET /users/{user_id}    │
└─────────────────────────┘
┌─ 文章 ─────────────────┐
│ POST /users/{id}/articles │
│ GET /articles           │
└─────────────────────────┘
```

不用 `tags`，所有路由混在一起不便于浏览。

### Router 之间共享依赖

APIRouter 可以在声明时绑定全局依赖，但**要注意它的真正用途**。

```python
router = APIRouter(
    prefix="/users",
    tags=["用户"],
    dependencies=[Depends(verify_token)],   # 每个路由执行前都先校验 token
)
```

**但是：** `dependencies` 里的依赖**只执行，不传参**。返回值不会注入到路由函数里。

```python
# ❌ 错误：dependencies 里的 get_db 虽然执行了，但 db 没有传进来
router = APIRouter(
    prefix="/users",
    dependencies=[Depends(get_db)],
)

@router.get("")
def list_users(pg: Pagination = Depends()):
    return db.query(User)...   # ← NameError: db 未定义！
```

**正确的做法：每个路由自己声明参数：**

```python
# ✅ 正确：每个路由函数明确声明自己需要什么
@router.get("")
def list_users(pg: Pagination = Depends(), db: Session = Depends(get_db)):
    return db.query(User).offset(pg.offset).limit(pg.page_size).all()

@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    ...
```

> `dependencies` 适合**有副作用但不需传值**的场景，比如：校验 token、记录访问日志、检查 IP 黑名单。获取 `db` Session 需要传值，所以每个路由参数声明最合适。

### include_router 时覆盖 prefix

```python
app.include_router(users_router, prefix="/api/v1")
```

这样即使 `users_router` 里定义了 `prefix="/users"`，最终路径是 `/api/v1/users`。适合给整个 API 加版本号。

---

**第八课结束。** 喊 **继续** 我开始第九课：Pydantic v2 进阶 —— model_validate, model_dump, 序列化技巧。

---

## 第九课：Pydantic v2 进阶 — 序列化与反序列化

### 三种创建模型的方式

```python
from pydantic import BaseModel

class UserResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    name: str
    email: str
```

| 方式 | 用法 | 数据来源 | 什么时候用 |
|------|------|---------|-----------|
| 构造器 | `UserResponse(id=1, name="小明", email="x@x.com")` | Python 参数 | 手动组装 |
| `model_validate` | `UserResponse.model_validate(orm_user)` | ORM 对象/dict | 从数据库查出来后 |
| `model_validate_json` | `UserResponse.model_validate_json(json_str)` | JSON 字符串 | 外部 JSON 解析 |

```python
# 方式 1：构造器
resp = UserResponse(id=1, name="小明", email="x@x.com")

# 方式 2：从 ORM 对象
user = db.query(User).first()
resp = UserResponse.model_validate(user)

# 方式 3：从 JSON 字符串
resp = UserResponse.model_validate_json('{"id":1,"name":"小明","email":"x@x.com"}')
```

> `model_validate` 是 Pydantic v2 替代 v1 的 `from_orm` 和 `parse_obj` 的统一方法。可以传 ORM 对象也可以传 dict。

### 三种导出模型的方式

```python
user = UserResponse(id=1, name="小明", email="x@x.com")

# 方式 1：导出 dict
data = user.model_dump()                    # {"id": 1, "name": "小明", "email": "x@x.com"}

# 方式 2：导出 JSON 字符串
json_str = user.model_dump_json()           # '{"id": 1, "name": "小明", "email": "x@x.com"}'

# 方式 3：导出 dict（只含部分字段）
data = user.model_dump(include={"id", "name"})  # {"id": 1, "name": "小明"}
```

### model_dump 的常用参数

```python
# 排除 None 字段
data = user.model_dump(exclude_none=True)

# 排除指定字段
data = user.model_dump(exclude={"hashed_password", "salt"})

# 只包含指定字段
data = user.model_dump(include={"id", "name"})

# 序列化为 JSON 兼容类型（datetime → str, Decimal → float）
data = user.model_dump(mode="json")
```

### 在 FastAPI 中的实际场景：敏感字段排除

```python
class UserInDB(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    name: str
    email: str
    hashed_password: str       # ← 这个不该返回给前端

# 在路由里手动排除
@app.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    data = UserInDB.model_validate(user)
    return data.model_dump(exclude={"hashed_password"})  # 手动排除
```

### datetime 字段序列化

```python
from datetime import datetime

class ArticleResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    title: str
    created_at: datetime | None = None   # ← datetime 字段

article = ArticleResponse(id=1, title="test", created_at=datetime.now())
article.model_dump()
# {"id": 1, "title": "test", "created_at": datetime.datetime(2026, 5, 28, ...)}

article.model_dump(mode="json")
# {"id": 1, "title": "test", "created_at": "2026-05-28T12:00:00"}

article.model_dump_json()
# '{"id": 1, "title": "test", "created_at": "2026-05-28T12:00:00"}'
```

> `model_dump()` 默认保留 Python 原生类型（datetime 对象），`model_dump(mode="json")` 自动转成 ISO 格式字符串。

### 自定义序列化

如果你想让日期格式是 `2026-05-28` 而不是 `2026-05-28T12:00:00`：

```python
from pydantic import BaseModel, field_serializer
from datetime import datetime

class ArticleResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    title: str
    created_at: datetime | None = None

    @field_serializer("created_at")
    def serialize_datetime(self, value: datetime | None) -> str | None:
        if value is None:
            return None
        return value.strftime("%Y-%m-%d %H:%M")
```

导出：

```python
article.model_dump(mode="json")
# {"id": 1, "title": "test", "created_at": "2026-05-28 12:00"}
```

### 嵌套模型的序列化

```python
class UserWithArticles(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    name: str
    articles: list[ArticleResponse] = []

# 嵌套导出自动递归
user_data = UserWithArticles.model_validate(db_user)
user_data.model_dump(mode="json")
# {
#   "id": 1,
#   "name": "小明",
#   "articles": [
#     {"id": 1, "title": "Pydantic", "created_at": "2026-05-28"},
#     {"id": 2, "title": "FastAPI", "created_at": "2026-05-27"}
#   ]
# }
```

> `model_dump(mode="json")` 逐层递归，嵌套多深就序列化多深。

### 序列化性能对比

| 方法 | 性能 | 推荐场景 |
|------|------|---------|
| `return orm_object` + `response_model` | 最快（FastAPI 内部处理） | 标准响应 |
| `model_dump()` | 中等 | 需要手动处理 dict |
| `model_dump(mode="json")` | 稍慢（datetime 等要转换） | 需要 JSON 兼容 dict |

> 实际项目中，95% 的情况直接用 `response_model` 就够了。需要手动操作时再用 `model_dump`。

### 总结：序列化路线图

```
ORM 对象
    │
    ▼
model_validate(user)          ← 从数据库到 Pydantic
    │
    ▼
Pydantic 实例
    │
    ├─→ FastAPI return + response_model   ← 自动序列化（推荐）
    ├─→ model_dump()                      ← 手动转 dict
    ├─→ model_dump(mode="json")           ← 转 JSON 兼容 dict
    └─→ model_dump_json()                 ← 转 JSON 字符串
```

---

**第九课结束。** 喊 **继续** 我开始第十课：总结与完整项目实战 —— 构建一个可运行的博客 API。

---

## 第十课：收官实战 — 完整博客 API

将前面 9 课知识串起来，构建一个可以运行的博客项目。

### 项目结构最终版

```
blog/
├── app/
│   ├── __init__.py
│   ├── main.py              # 应用入口
│   ├── database.py          # 数据库连接
│   ├── models.py            # SQLAlchemy 模型
│   ├── schemas.py           # Pydantic 模型
│   └── routers/
│       ├── __init__.py
│       ├── users.py         # 用户路由
│       └── articles.py      # 文章路由
├── static/                  # 上传文件存放
└── requirements.txt
```

### requirements.txt

```
fastapi==0.115.0
uvicorn==0.30.0
sqlalchemy==2.0.35
pydantic==2.9.0
```

### app/database.py

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

SQLALCHEMY_DATABASE_URL = "sqlite:///./blog.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### app/models.py

```python
from sqlalchemy import String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(unique=True)
    hashed_password: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    articles: Mapped[list["Article"]] = relationship(back_populates="author")

class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    author: Mapped["User"] = relationship(back_populates="articles")
```

> 相比第五课，添加了 `created_at` 时间戳字段，用 `server_default=func.now()` 让数据库自动填充。

### app/schemas.py

```python
from pydantic import BaseModel, Field
from datetime import datetime

# ---------- 公共 ----------
class Pagination(BaseModel):
    model_config = {"extra": "forbid"}
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

# ---------- 用户 ----------
class UserCreate(BaseModel):
    model_config = {"extra": "forbid", "str_strip_whitespace": True}
    name: str = Field(min_length=2, max_length=50)
    email: str
    password: str = Field(min_length=6)

class UserResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    name: str
    email: str
    created_at: datetime | None = None

class UserWithArticles(UserResponse):
    articles: list["ArticleResponse"] = []

# ---------- 文章 ----------
class ArticleCreate(BaseModel):
    model_config = {"extra": "forbid"}
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)

class ArticleResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    title: str
    content: str
    created_at: datetime | None = None
    user_id: int

class ArticleWithAuthor(ArticleResponse):
    author: UserResponse | None = None
```

### app/routers/users.py

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from hashlib import sha256

from database import get_db
from models import User
from schemas import UserCreate, UserResponse, UserWithArticles, Pagination

router = APIRouter(prefix="/users", tags=["用户"])

@router.post("", response_model=UserResponse, status_code=201)
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    exists = db.query(User).filter(User.email == user_data.email).first()
    if exists:
        raise HTTPException(409, "邮箱已注册")
    db_user = User(
        name=user_data.name,
        email=user_data.email,
        hashed_password=sha256(user_data.password.encode()).hexdigest(),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("", response_model=list[UserResponse])
def list_users(pg: Pagination = Depends(), db: Session = Depends(get_db)):
    return db.query(User).offset(pg.offset).limit(pg.page_size).all()

@router.get("/{user_id}", response_model=UserWithArticles)
def get_user(user_id: int, db: Session = Depends(get_db)):
    from sqlalchemy.orm import selectinload
    user = db.query(User).options(selectinload(User.articles)).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "用户不存在")
    return user
```

### app/routers/articles.py

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from database import get_db
from models import Article, User
from schemas import ArticleCreate, ArticleResponse, ArticleWithAuthor, Pagination

router = APIRouter(prefix="/users/{user_id}/articles", tags=["文章"])
router_public = APIRouter(prefix="/articles", tags=["文章"])

@router.post("", response_model=ArticleResponse, status_code=201)
def create_article(user_id: int, article_data: ArticleCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "用户不存在")
    db_article = Article(title=article_data.title, content=article_data.content, user_id=user_id)
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    return db_article

@router_public.get("", response_model=list[ArticleResponse])
def list_articles(pg: Pagination = Depends(), db: Session = Depends(get_db)):
    return db.query(Article).offset(pg.offset).limit(pg.page_size).all()

@router_public.get("/{article_id}", response_model=ArticleWithAuthor)
def get_article(article_id: int, db: Session = Depends(get_db)):
    article = db.query(Article).options(selectinload(Article.author)).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(404, "文章不存在")
    return article
```

### app/main.py

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers.users import router as users_router
from routers.articles import router as articles_user_router
from routers.articles import router_public as articles_router

app = FastAPI(title="博客 API", description="FastAPI + Pydantic + SQLAlchemy 实战")

# CORS
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# 建表
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

# 注册路由
app.include_router(users_router)
app.include_router(articles_user_router)
app.include_router(articles_router)
```

### 启动

```bash
cd blog
uvicorn app.main:app --reload
```

### 测试流程

```bash
# 1. 创建用户
curl -X POST http://127.0.0.1:8000/users \
  -H "Content-Type: application/json" \
  -d '{"name": "小明", "email": "x@x.com", "password": "123456"}'

# 2. 创建文章
curl -X POST http://127.0.0.1:8000/users/1/articles \
  -H "Content-Type: application/json" \
  -d '{"title": "FastAPI 入门", "content": "这是一篇入门教程"}'

# 3. 查用户（带文章列表）
curl http://127.0.0.1:8000/users/1
# → 返回用户信息 + articles 数组

# 4. 查文章（带作者）
curl http://127.0.0.1:8000/articles/1
# → 返回文章信息 + author 对象
```

### 你学到的全部知识 — 一句话总结

```
用户请求 → (Path/Query/Pydantic 校验) → (APIRouter 路由) → (Depends 注入 db)
        → (SQLAlchemy CRUD) → (response_model 过滤) → JSON 响应
```

这是 FastAPI + Pydantic + SQLAlchemy 的**完整请求生命周期**，10 课全部覆盖。实际项目中你还会遇到认证、测试、部署等主题——但核心架构就是这 10 课的内容，后面的都是添砖加瓦。

---

**全文完。** 10 课全部结束，你已经掌握了 FastAPI 从零到实战的核心能力。遇到具体问题随时问我。