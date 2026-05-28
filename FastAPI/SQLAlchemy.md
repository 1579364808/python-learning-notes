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