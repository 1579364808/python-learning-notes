# SQLAlchemy ORM 进阶操作指南 (FastAPI)

本笔记涵盖了 SQLAlchemy 在 FastAPI 中的核心进阶用法，包括条件筛选、模糊查询、聚合统计、分页处理及 CRUD 的高效实现。

---

## 1. 条件查询 (比较运算符)

在 `.where()` 中直接使用 Python 比较运算符。SQLAlchemy 会自动将其转换为相应的 SQL 条件。

### 核心语法
```python
from sqlalchemy import select

# 大于 (>) / 小于等于 (<=) / 不等于 (!=)
stmt = select(User).where(User.age > 18)
stmt = select(User).where(User.age <= 30)
stmt = select(User).where(User.username != "admin")

# 多条件查询 (AND 关系)
# 多个参数之间用逗号隔开，即代表 AND
stmt = select(User).where(User.age > 18, User.username != "admin")
```

### FastAPI 接口示例
```python
@app.get("/users/filter/age")
async def filter_users_by_age(min_age: int, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.age > min_age)
    result = await db.execute(stmt)
    return result.scalars().all()
```

---

## 2. 模糊查询 (LIKE)

用于搜索包含特定字符的数据。

### 核心方法
*   `.like()`：严格匹配大小写。
*   `.ilike()`：忽略大小写 (Insensitive Like)。

### 语法示例
```python
# 包含关键词: %关键词%
stmt = select(User).where(User.username.like("%张%"))

# 以关键词开头: 关键词%
stmt = select(User).where(User.username.like("张%"))

# 忽略大小写的模糊查询
stmt = select(User).where(User.username.ilike("%python%"))
```

---

## 3. 聚合查询 (Aggregate)

使用 `sqlalchemy.func` 提供的数据库内置函数进行统计。

### 常用函数
```python
from sqlalchemy import select, func

# 统计总数 (COUNT)
stmt = select(func.count(User.id))

# 平均值 (AVG) / 求和 (SUM)
stmt = select(func.avg(User.age))
stmt = select(func.sum(User.score))

# 最大值 (MAX) / 最小值 (MIN)
stmt = select(func.max(User.age))
```

### 结果获取
对于返回单行单列结果的聚合查询，使用 `.scalar()` 直接提取数值：
```python
result = await db.execute(stmt)
total = result.scalar()  # 直接拿到数字
```

---

## 4. 分页查询 (Pagination)

通过 `.limit()` (截取数量) 和 `.offset()` (跳过偏移量) 实现。

### 分页公式
*   `limit = size` (每页条数)
*   `offset = (page - 1) * size` (跳过前几页的条数)

### 实战代码
```python
@app.get("/users/list/paged")
async def get_paged_users(page: int = 1, size: int = 10, db: AsyncSession = Depends(get_db)):
    skip = (page - 1) * size
    stmt = select(User).offset(skip).limit(size)
    
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    return {"page": page, "size": size, "data": users}
```

---

## 5. 新增数据 (Create)

### 单条新增
```python
new_user = User(username="name", email="email@example.com")
db.add(new_user)
await db.commit()
await db.refresh(new_user) # 刷新以获取数据库生成的 ID
```

### 批量新增 (效率更高)
```python
user_list = [User(...), User(...), User(...)]
db.add_all(user_list)
await db.commit()
```

---

## 6. 更新数据 (Update)

### 方式一：先查后改 (推荐)
适合简单的单个对象修改。SQLAlchemy 会自动追踪已查询对象的属性变化。
```python
# 1. 查出对象
user = await db.get(User, user_id)
# 2. 直接修改属性
if user:
    user.username = "new_name"
    # 3. 提交
    await db.commit()
```

### 方式二：直接指令更新 (进阶)
适合批量更新或高性能场景，无需先加载数据到内存。
```python
from sqlalchemy import update

stmt = update(User).where(User.id == user_id).values(email="new_email@test.com")
await db.execute(stmt)
await db.commit()
```

---

## 7. 删除数据 (Delete)

### 方式一：先查后删
```python
user = await db.get(User, user_id)
if user:
    await db.delete(user)
    await db.commit()
```

### 方式二：条件直接删除
```python
from sqlalchemy import delete

stmt = delete(User).where(User.username == "test_user")
await db.execute(stmt)
await db.commit()
```

---

## 核心概念总结
| 操作 | 关键字/方法 | 结果提取 |
| :--- | :--- | :--- |
| **查询全部** | `select(Model)` | `.scalars().all()` |
| **条件查询** | `.where(条件)` | `.scalars().all()` |
| **获取单个** | `.first()` / `.get()` | 直接对象 |
| **统计数值** | `func.count()` | `.scalar()` |
| **提交变更** | `db.commit()` | - |
| **物理删除** | `db.delete(obj)` | 需 commit 生效 |
