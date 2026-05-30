# SQLAlchemy 学习笔记

---

## 第一课：SQLAlchemy 是什么？为什么需要它？

### 没有 ORM 的时候

假设你直接操作 SQLite：

```python
import sqlite3

conn = sqlite3.connect("blog.db")
cursor = conn.cursor()

# 插入用户
cursor.execute("INSERT INTO users (name, email) VALUES (?, ?)", ("小明", "x@x.com"))

# 查询用户
cursor.execute("SELECT id, name, email FROM users WHERE id = ?", (1,))
row = cursor.fetchone()  # (1, '小明', 'x@x.com')
```

**问题：**
- SQL 是字符串，写错了没有提示
- 取出来的是元组 `(1, '小明', 'x@x.com')`，要用 `row[1]` 取值
- 每个表都要手写 CRUD 的 SQL

### 有了 ORM 之后

ORM（对象关系映射）让你**用 Python 对象操作数据库**：

```python
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str]

# 插入
user = User(name="小明", email="x@x.com")
db.add(user)
db.commit()

# 查询
user = db.query(User).filter(User.id == 1).first()
print(user.name)   # "小明"，不是 row[1]
```

### SQLAlchemy 的两层结构

```
你的代码（ORM 层）
    ↓
Session    ← 你打交道最多的：增删改查都通过它
    ↓
Engine     ← 连接数据库、执行 SQL
    ↓
Database (SQLite / PostgreSQL / MySQL)
```

| 组件 | 你什么时候用 | 示例 |
|------|-------------|------|
| `Engine` | 启动时配一次 | `create_engine("sqlite:///blog.db")` |
| `Session` | 每个请求 | `db.query(User)`、`db.add(obj)` |
| `Model` | 定义表结构 | `class User(Base): ...` |

### 和 Pydantic 的本质区别

```python
# SQLAlchemy — 管数据库
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(unique=True)

# Pydantic — 管 API
class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    email: str
```

| | SQLAlchemy | Pydantic |
|---|---|---|
| 存数据 | 写入数据库 | 内存校验后丢弃 |
| 核心方法 | `db.add()`、`db.commit()` | `.model_validate()`、`.model_dump()` |
| 主键 | 通常有（id） | 按需（响应体才要） |
| 约束类型 | NOT NULL、UNIQUE、FK | `min_length`、`ge`、`pattern` |

> **一句话：** SQLAlchemy 管"存"，Pydantic 管"传"。两者各行其是，你的代码在中间做转换。

### 预备知识

| 概念 | 含义 |
|------|------|
| 表 | 数据的容器，类似 Excel 工作表 |
| 行 | 一条记录，类似 Excel 的一行 |
| 主键 | 唯一标识一行（通常是 id） |
| 外键 | 指向另一个表的主键 |
| 索引 | 加速查询 |

---

**第一课结束。** 喊 **继续** 我开始第二课：连接配置、Engine、Session 与快速建表。

---

## 第二课：Engine、Session 与建表

### 快速起步：完整的数据库配置

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column

# 1. 创建 Engine（连接数据库）
engine = create_engine("sqlite:///./blog.db", echo=True)

# 2. 创建 Session 工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. 定义基类（所有模型的父类）
class Base(DeclarativeBase):
    pass

# 4. 定义模型（一张表）
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str]

# 5. 建表
Base.metadata.create_all(bind=engine)
```

这 5 步就是 SQLAlchemy 的标准启动流程。我们来逐条拆解。

### 1. Engine — 数据库连接

```python
from sqlalchemy import create_engine

# SQLite（开发用）
engine = create_engine("sqlite:///./blog.db")

# 打印 SQL 日志（调试用）
engine = create_engine("sqlite:///./blog.db", echo=True)

# PostgreSQL（生产用）
# engine = create_engine("postgresql://user:password@localhost/blogdb")

# MySQL
# engine = create_engine("mysql://user:password@localhost/blogdb")
```

> `echo=True` 会在控制台打印所有执行的 SQL 语句，开发调试很有用。

### 2. Session — 数据库会话

```python
from sqlalchemy.orm import sessionmaker

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

`SessionLocal` 是一个**工厂**，每次调用返回一个新的 `Session`。

```python
# 创建 Session
db = SessionLocal()

# 用 Session 操作数据库
user = User(name="小明", email="x@x.com")
db.add(user)
db.commit()      # 提交事务
db.close()       # 关闭 Session
```

| Session 方法                 | 作用                 |
| -------------------------- | ------------------ |
| `db.add(obj)`              | 把对象加入 Session（待插入） |
| `db.add_all([obj1, obj2])` | 批量加入               |
| `db.commit()`              | 提交事务，写入数据库         |
| `db.refresh(obj)`          | 从数据库刷新对象（拿到生成的 id） |
| `db.delete(obj)`           | 标记删除               |
| `db.close()`               | 关闭 Session         |
| `db.rollback()`            | 回滚事务               |

### 3. 创建和删除表

```python
# 建表（只建不存在的表）
Base.metadata.create_all(bind=engine)

# 删表（慎用！）
Base.metadata.drop_all(bind=engine)
```

> `create_all()` 是幂等的——表已存在就不会重复创建。

### 4. 完整的 CRUD 操作

```python
# 创建 Engine + Session
engine = create_engine("sqlite:///./blog.db")
SessionLocal = sessionmaker(bind=engine)

# 建表
Base.metadata.create_all(bind=engine)

# 打开 Session
db = SessionLocal()

# ----- CREATE -----
user = User(name="小明", email="x@x.com")
db.add(user)
db.commit()
db.refresh(user)
print(user.id)      # 1（数据库自增）

# ----- READ (单条) -----
user = db.query(User).filter(User.id == 1).first()
print(user.name)    # "小明"

# ----- READ (多条) -----
users = db.query(User).all()            # 全部
users = db.query(User).limit(10).all()  # 前 10 条

# ----- UPDATE -----
user = db.query(User).filter(User.id == 1).first()
user.name = "小红"
db.commit()

# ----- DELETE -----
user = db.query(User).filter(User.id == 1).first()
db.delete(user)
db.commit()

# 关闭
db.close()
```

### 5. 在 FastAPI 中的标准用法

这就是 FastAPI 的 `Depends(get_db)` 模式：

```python
from fastapi import FastAPI, Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column

# ---------- 配置 ----------
engine = create_engine("sqlite:///./blog.db")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str]

# ---------- 依赖注入 ----------
def get_db():
    db = SessionLocal()
    try:
        yield db        # ← 路由函数在这里拿到 db
    finally:
        db.close()      # ← 请求结束自动关闭

# ---------- 路由 ----------
app = FastAPI()

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

@app.post("/users")
def create_user(name: str, email: str, db: Session = Depends(get_db)):
    user = User(name=name, email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "name": user.name, "email": user.email}
```

> 注意这里的 **生命循环**：每个请求 → 创建 Session → 操作数据库 → 请求结束 → 关闭 Session。

### 6. Session vs Pydantic 模型

在路由中，你的数据流是：

```
Pydantic 校验请求体  →  创建 SQLAlchemy 对象  →  Session 写入
                                                      ↓
JSON 响应            ←  Pydantic 格式化      ←  Session 查询
```

```python
@app.post("/users")
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    # 1. Pydantic → SQLAlchemy
    db_user = User(name=user_data.name, email=user_data.email)

    # 2. Session 写入
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # 3. SQLAlchemy → Pydantic 响应
    return UserResponse(id=db_user.id, name=db_user.name, email=db_user.email)
```

---

**第二课结束。** 喊 **继续** 我开始第三课：Column 类型、约束与 Mapped 详解。

---

## 第三课：字段类型与约束

### Mapped 映射规则

SQLAlchemy 2.0 核心写法：

```python
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    age: Mapped[int | None]
    score: Mapped[float] = mapped_column(default=0.0)
```

| 声明 | 含义 | 数据库效果 |
|------|------|-----------|
| `Mapped[int]` | NOT NULL int | `INTEGER NOT NULL` |
| `Mapped[int \| None]` | 可为 NULL | `INTEGER` |
| `Mapped[str]` | NOT NULL str | `VARCHAR NOT NULL` |
| `mapped_column(primary_key=True)` | 主键 | `PRIMARY KEY` |
| `mapped_column(unique=True)` | 唯一约束 | `UNIQUE` |
| `mapped_column(default=0)` | 默认值 | 由 SQLAlchemy 在 INSERT 时填入 |

> `Mapped[str]` 相当于 `Column(String, nullable=False)`，更简洁。**类型注解本身就表达了可空性。**

### 常见字段类型

```python
from sqlalchemy import String, Text, DateTime, Boolean, Integer, Float

class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))      # VARCHAR(100)
    content: Mapped[str] = mapped_column(Text)            # TEXT
    view_count: Mapped[int] = mapped_column(default=0)
    is_published: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, onupdate=datetime.now)
```

| Python 类型 | 数据库类型 | 说明 |
|-------------|-----------|------|
| `Mapped[int]` | `INTEGER` | 整数 |
| `Mapped[str]` | `VARCHAR` | 字符串 |
| `Mapped[str] = mapped_column(Text)` | `TEXT` | 长文本 |
| `Mapped[float]` | `FLOAT` | 浮点数 |
| `Mapped[bool]` | `BOOLEAN` | 布尔值 |
| `Mapped[datetime]` | `DATETIME` | 日期时间 |

### 和 Pydantic 对比

```python
# SQLAlchemy
class User(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    age: Mapped[int] = mapped_column(default=18)

# Pydantic
class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    age: int = Field(default=18, ge=0, le=150)
```

| 目标 | SQLAlchemy | Pydantic |
|------|-----------|----------|
| 值不能为空 | `Mapped[str]`（不含 `\| None`） | `str`（不写 default） |
| 默认值 | `mapped_column(default=18)` | `Field(default=18)` |
| 最大长度 | `mapped_column(String(50))` | `Field(max_length=50)` |
| 唯一 | `unique=True` | ❌ 只有数据库能保证 |
| 范围 | ❌ 不支持 | `Field(ge=0, le=150)` |

> **边界清晰：** SQLAlchemy 管数据库约束，Pydantic 管应用层校验。两者互补，不是替代。

---

**第三课结束。** 喊 **继续** 我开始第四课：Query 查询 —— filter、排序、分页与条件组合。

---

## 第四课：Query 查询 — 查数据是后端核心

### 基础查询

```python
# 查全部
db.query(User).all()

# 查一条（根据主键）
db.query(User).get(1)            # 按 ID 查（2.0 中推荐用 filter）
db.query(User).filter(User.id == 1).first()

# 查多条，限制数量
db.query(User).limit(10).all()

# 查第一条
db.query(User).first()

# 查数量
db.query(User).count()
```

### where / filter — 条件筛选

```python
# 等于
db.query(User).filter(User.name == "小明").all()

# 不等于
db.query(User).filter(User.name != "小明").all()

# 大于 / 小于
db.query(Article).filter(Article.view_count > 100).all()
db.query(Article).filter(Article.created_at >= "2026-01-01").all()

# IN
db.query(User).filter(User.id.in_([1, 2, 3])).all()

# NOT IN
db.query(User).filter(~User.id.in_([1, 2, 3])).all()

# LIKE（模糊查询）
db.query(User).filter(User.name.like("%小%")).all()

# IS NULL
db.query(Article).filter(Article.content == None).all()
# 或
db.query(Article).filter(Article.content.is_(None)).all()
```

### 多条件组合

```python
# AND（多个 filter 用逗号）
db.query(Article).filter(
    Article.title.contains("Python"),
    Article.view_count > 50,
    Article.is_published == True,
).all()

# OR
from sqlalchemy import or_

db.query(User).filter(
    or_(
        User.name == "小明",
        User.name == "小红",
    )
).all()

# AND + OR 混合
db.query(Article).filter(
    Article.is_published == True,
    or_(
        Article.title.contains("Python"),
        Article.title.contains("FastAPI"),
    ),
).all()
```

### 排序

```python
# 升序
db.query(Article).order_by(Article.created_at).all()

# 降序
db.query(Article).order_by(Article.created_at.desc()).all()

# 多字段排序
db.query(Article).order_by(
    Article.is_published.desc(),
    Article.created_at.desc(),
).all()
```

### 分页

```python
page = 2
page_size = 10

# offset = (page - 1) * page_size
articles = db.query(Article).order_by(
    Article.created_at.desc()
).offset((page - 1) * page_size).limit(page_size).all()

# 同时返回总数
total = db.query(Article).count()
```

### 结合 FastAPI + Pydantic 分页

```python
# schemas.py
from pydantic import BaseModel, Field

class Pagination(BaseModel):
    model_config = {"extra": "forbid"}
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

# routers/articles.py
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/articles", tags=["文章"])

@router.get("")
def list_articles(
    pg: Pagination = Depends(),
    db: Session = Depends(get_db),
):
    total = db.query(Article).count()
    articles = db.query(Article).order_by(
        Article.created_at.desc()
    ).offset(pg.offset).limit(pg.page_size).all()

    return {
        "total": total,
        "page": pg.page,
        "page_size": pg.page_size,
        "items": articles,
    }
```

> 返回值如果是 list[ORM 对象]，FastAPI 不知道如何序列化。所以要么用 `response_model`，要么手动转 dict。

### select() — 2.0 新查询风格

SQLAlchemy 2.0 提供了 `select()` 函数作为全新的查询方式：

```python
from sqlalchemy import select

# 旧风格（1.x）
user = db.query(User).filter(User.id == 1).first()

# 新风格（2.0）
stmt = select(User).where(User.id == 1)
user = db.execute(stmt).scalar_one_or_none()
```

新风格看起来更啰嗦，但好处是 **select() 可以脱离 Session 构建**，后续课程会用到。

**当前课程建议继续用 `db.query()`**，它更简洁直观。等后期需要复杂查询再切换到 `select()`。

### 查询结果转 Pydantic 响应

```python
@app.get("/users", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()
    # ↑ response_model 自动完成 ORM → Pydantic

@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "用户不存在")
    return user
```

> `response_model=UserResponse` + `from_attributes=True` = 无需手动调用 `model_validate`，FastAPI 自动处理。

---

**第四课结束。** 喊 **继续** 我开始第五课：Relationships —— 外键、一对多、back_populates。

---

## 第五课：Relationships — 外键与关联

### 场景：用户有多个文章

单表不够了——用户和文章是"一对多"关系：

- 一个用户可以有**多篇**文章
- 一篇文章**属于一个**用户

数据库用**外键 + 两张表**表达：

```
users 表                    articles 表
┌─────┬──────┬───────┐     ┌────┬──────────┬──────────┬──────────┐
│ id  │ name │ email │     │ id │  title   │ content  │ user_id  │──┐
├─────┼──────┼───────┤     ├────┼──────────┼──────────┼──────────┤  │
│  1  │ 小明 │ x@x   │     │  1 │ FastAPI  │ 内容...  │    1     │──┼──FK
│  2  │ 小红 │ h@h   │     │  2 │ Pydantic │ 内容...  │    1     │──┘
└─────┴──────┴───────┘     │  3 │ SQLAlch..│ 内容...  │    2     │
                           └────┴──────────┴──────────┴──────────┘
```

### 建表：Foreign Key + relationship

```python
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str]

    # "User 有多篇 Article"——一对多的"多"方
    articles: Mapped[list["Article"]] = relationship(back_populates="author")

class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    content: Mapped[str]

    # 外键 —— 指向 users 表的主键
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # "Article 属于一个 User"——一对多的"一"方
    author: Mapped["User"] = relationship(back_populates="articles")
```

### 三个关键元素

```python
# 1. ForeignKey("users.id") — 数据库层面的约束
user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

# 2. relationship() — ORM 层面的关联（让你能用 .author 访问）
author: Mapped["User"] = relationship(back_populates="articles")

# 3. back_populates — 双向绑定，名字要互相匹配
```

| 元素 | 作用 | 写在哪儿 |
|------|------|---------|
| `ForeignKey` | 数据库外键约束 | "多"的那张表（Article） |
| `relationship` | Python 对象导航 | 两边都写 |
| `back_populates` | 双向关联的名字 | 两边互指 |

> `ForeignKey` 是**数据库真实约束**——它保证 `user_id` 的值必须在 `users.id` 中存在，不存在就报错。`relationship` 是 **ORM 层的便利工具**——让你用 `article.author` 和 `user.articles` 访问关联数据。

### 如何使用 relationship

```python
# 创建关联对象（给 user_id 赋值）
user = User(name="小明", email="x@x.com")
db.add(user)
db.commit()

article = Article(title="FastAPI", content="...", user_id=user.id)
db.add(article)
db.commit()

# 正向导航：文章 → 作者
article = db.query(Article).first()
print(article.author.name)       # "小明"（自动从 user_id 查到 User）
print(article.author.email)      # "x@x.com"

# 反向导航：用户 → 文章列表
user = db.query(User).first()
for article in user.articles:    # 自动查询该用户的所有文章
    print(article.title)
```

### 在 FastAPI + Pydantic 中使用

```python
# schemas.py
from pydantic import BaseModel

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
    articles: list[ArticleResponse] = []   # 嵌套！关联文章的列表
```

路由中直接返回 ORM 对象，`response_model` 自动映射：

```python
@app.get("/users/{user_id}", response_model=UserWithArticles)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "用户不存在")
    return user   # user.articles 会被自动映射到 UserWithArticles.articles
```

返回的 JSON：

```json
{
    "id": 1,
    "name": "小明",
    "email": "x@x.com",
    "articles": [
        {"id": 1, "title": "FastAPI", "content": "...", "user_id": 1},
        {"id": 2, "title": "Pydantic", "content": "...", "user_id": 1}
    ]
}
```

### ⚠️ N+1 问题

上面的写法有一个隐患：

```python
user = db.query(User).first()
# 此时只是查了 users 表（1 次查询）
print(len(user.articles))
# 访问 user.articles 时会再查 articles 表（N 次查询）
```

这就是 **N+1 问题**：1 次查用户 + N 次查文章。

**解决方法：用 selectinload 预加载**

```python
from sqlalchemy.orm import selectinload

user = db.query(User).options(
    selectinload(User.articles)    # 一次查出所有关联文章
).filter(User.id == 1).first()

# 现在访问 user.articles 不再触发额外查询
print(user.articles[0].title)
```

> **什么时候用 selectinload：** 当你**确定**会用关联数据时（比如响应模型里嵌套了子列表）。如果只是判断有没有关联，用 `lazy="select"`（默认）就够了。

### 关于 relationship 的 FAQ

**Q: 创建文章时，可以用 article.author = user 而不是 user_id 吗？**

```python
user = db.query(User).first()
article = Article(title="test", content="...")
article.author = user        # ✓ relationship 让你直接赋对象
db.add(article)
db.commit()
```

**Q: 删除用户时文章会怎样？**

默认情况下，`user_id` 是外键，如果文章引用了用户，直接删用户会报外键错误。需要先删文章或设置级联：

```python
class Article(Base):
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
```

---

**第五课结束。** 喊 **继续** 我开始第六课：级联删除、多对多关系与进阶关联。

---

## 第六课：级联删除与多对多

### 级联删除 — 删用户时自动删他的文章

当前的问题：如果用户有文章，直接删用户会报外键错误。

```python
user = db.query(User).filter(User.id == 1).first()
db.delete(user)
db.commit()   # ❌ IntegrityError: 还有文章引用这个用户
```

**方案一：先删文章，再删用户**

```python
# 手动删所有关联文章
db.query(Article).filter(Article.user_id == user_id).delete()
# 再删用户
user = db.query(User).filter(User.id == user_id).first()
db.delete(user)
db.commit()
```

**方案二：数据库级联（推荐）**

```python
class Article(Base):
    __tablename__ = "articles"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")   # ← 级联删除
    )
```

加上 `ondelete="CASCADE"` 后，删除用户时数据库**自动删除**所有关联的文章。

> **注意：** `ondelete="CASCADE"` 是**数据库层面的行为**，不是 ORM 的。直接在数据库工具里删用户也会触发。

**方案三：ORM 级联（relationship 上设置）**

```python
class User(Base):
    __tablename__ = "users"

    articles: Mapped[list["Article"]] = relationship(
        back_populates="author",
        cascade="all, delete-orphan",   # ← ORM 级联
    )
```

区别：

| 方案 | 设置位置 | 触发条件 | 推荐？ |
|------|---------|---------|-------|
| `ondelete="CASCADE"` | `ForeignKey` 上 | 数据库层删除时 | ✅ 推荐 |
| `cascade="all, delete-orphan"` | `relationship` 上 | ORM `session.delete()` 时 | 视场景 |
| 手动先删后删 | 业务代码 | 你手动写 | 最可控 |

> 大多数项目直接用 `ondelete="CASCADE"` 最简单。如果不想自动删（比如保留文章但 user_id 置空），用 `ondelete="SET NULL"`。

### 多对多关系 — 文章和标签

一对多用**外键**就够了。多对多需要一张**中间表**：

```
文章 1  ←→  标签 A
         ←→  标签 B
文章 2  ←→  标签 B
         ←→  标签 C
```

```
article_tags（中间表）
┌────────────┬──────────┐
│ article_id │ tag_id   │
├────────────┼──────────┤
│     1      │    1     │
│     1      │    2     │
│     2      │    2     │
│     2      │    3     │
└────────────┴──────────┘
```

### 多对多实现

```python
from sqlalchemy import Table, Column, ForeignKey

# 中间表（不是 Model，只是一张表）
article_tag = Table(
    "article_tags",
    Base.metadata,
    Column("article_id", ForeignKey("articles.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True),
)

class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    content: Mapped[str]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    tags: Mapped[list["Tag"]] = relationship(
        secondary=article_tag,     # ← 中间表
        back_populates="articles",
    )

class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)

    articles: Mapped[list["Article"]] = relationship(
        secondary=article_tag,
        back_populates="tags",
    )
```

**关键区别：**

| | 一对多 | 多对多 |
|---|---|---|
| 额外表 | 不需要 | 需要**中间表** |
| 外键在 | "多"的那张表 | 中间表 |
| `relationship` | 不用 `secondary` | 要写 `secondary=中间表` |
| 访问方式 | `user.articles` | `article.tags` |

### 多对多的增删改查

```python
# 创建标签
tag_python = Tag(name="Python")
tag_fastapi = Tag(name="FastAPI")
db.add_all([tag_python, tag_fastapi])
db.commit()

# 创建文章并关联标签
article = Article(title="FastAPI 入门", content="...")
article.tags = [tag_python, tag_fastapi]  # ← 直接赋值列表
db.add(article)
db.commit()

# 查询文章，自动带出标签
article = db.query(Article).first()
for tag in article.tags:
    print(tag.name)    # "Python", "FastAPI"

# 查询标签，自动带出文章
tag = db.query(Tag).filter(Tag.name == "Python").first()
for article in tag.articles:
    print(article.title)

# 给文章加一个新标签
new_tag = Tag(name="SQLAlchemy")
db.add(new_tag)
article.tags.append(new_tag)   # ← 和操作列表一样
db.commit()
```

### 多对多的 N+1 问题

和一对多一样，多对多也有 N+1 问题：

```python
# ❌ 会触发 N+1
articles = db.query(Article).all()
for a in articles:
    print(a.tags)   # 每个 article 都触发一次查询

# ✅ 预加载
from sqlalchemy.orm import selectinload

articles = db.query(Article).options(
    selectinload(Article.tags)
).all()
for a in articles:
    print(a.tags)   # 一次查出所有关联
```

### 多对多 + FastAPI + Pydantic 完整示例

```python
# schemas.py
class TagResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    name: str

class ArticleWithTags(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    title: str
    content: str
    tags: list[TagResponse] = []

# main.py
@app.get("/articles/{article_id}", response_model=ArticleWithTags)
def get_article(article_id: int, db: Session = Depends(get_db)):
    article = db.query(Article).options(
        selectinload(Article.tags)
    ).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(404, "文章不存在")
    return article
```

返回：

```json
{
    "id": 1,
    "title": "FastAPI 入门",
    "content": "...",
    "tags": [
        {"id": 1, "name": "Python"},
        {"id": 2, "name": "FastAPI"}
    ]
}
```

---

**第六课结束。** 喊 **继续** 我开始第七课：select() 新式查询与聚合查询（count、group_by、having）。