# SQLAlchemy vs JPA —— `db.add()` 完全解读

> 背景：Java + Spring Boot + JPA → 转 Python FastAPI + SQLAlchemy

---

## 核心一句话

`db.add(user)` 等价于 Java JPA 的 `entityManager.persist(user)` / `entityManager.merge(user)`，作用是**把一个对象注册到当前 Session，告诉 ORM"这个对象我要存/改"**。

---

## Java JPA vs Python SQLAlchemy 概念对照表

| 概念 | Java/JPA/Hibernate | Python/SQLAlchemy |
|---|---|---|
| 会话/上下文 | `EntityManager` | `AsyncSession`（即参数 `db`） |
| 注册新对象 | `em.persist(user)` | `db.add(user)` |
| 加载对象 | `em.find(User.class, id)` | `await db.execute(select(User).where(...))` |
| 提交事务 | `@Transactional` / `em.getTransaction().commit()` | `await db.commit()` |
| 刷新对象 | `em.refresh(user)` | `await db.refresh(user)` |
| 自动脏检查 | ✅ Hibernate 自动检测 | ❌ 默认不追踪，需要 `db.add(obj)` 告诉它 |

---

## 关键差异：脏检查（Dirty Checking）

### Java/Hibernate
```java
@Transactional
public void changePassword(Long userId, String newPwd) {
    User user = em.find(User.class, userId);  // 持久态
    user.setPassword(newPwd);                  // 改字段，自动生成 UPDATE
}
```
Hibernate 自动检测持久态对象的属性变化，**无需显式调用任何方法**。

### Python/SQLAlchemy
```python
async def change_password(db, user, old_pwd, new_pwd):
    user.password = hashed_new_pwd
    # 不加 db.add(user) → SQLAlchemy 不知道对象被改了
    db.add(user)       # 重新附加到会话，标记为"脏"
    await db.commit()  # 这时才生成 UPDATE
```

**为什么 SQLAlchemy 需要手动 add？**
因为 `user` 是通过 `db.execute(select(...))` 查出来的，在函数间传递时 Python 无法像 Java 那样自动追踪对象的"持久态"生命周期。`db.add()` 就是显式告诉 Session："这个对象我要改，请跟踪它。"

---

## 忘了写 `db.add(user)` 会怎样？

```python
user.password = hashed_new_pwd
# 忘了 db.add(user)
await db.commit()  # ✅ 不会报错，但 UPDATE 不会发出！
```
**静默失败** —— 不像 Java 抛异常，而是不报错也不更新，非常坑。

---

## `db.add()` 干了什么？

### 对象状态变化

| 状态 | 含义 | 触发方式 |
|---|---|---|
| **Transient（临时）** | Python 内存对象，数据库没有对应行 | `User(name="abc")` |
| **Pending（待定）** | 已 `add` 但未 `commit` | `db.add(obj)` |
| **Persistent（持久）** | 已 `commit`，与数据库行关联 | `commit()` 后 |
| **Detached（分离）** | 曾经是持久，但会话关闭/对象被传出 | 函数间传递时 |

`db.add(user)` 就是把对象从 **Detached → Pending**，让 Session 开始跟踪它的变化。

### 对 new 对象 vs 对已有对象

```python
# 场景 A：新建用户 → 生成 INSERT
user = User(username="张三", password="xxx")  # Transient
db.add(user)                                   # Pending → commit 时 INSERT

# 场景 B：修改已有用户 → 生成 UPDATE
user = await get_user_by_username(db, "张三")  # Detached
db.add(user)                                   # Pending → commit 时 UPDATE
```

---

## Java 的事务注解 vs Python 手动事务

### Java
```java
@Transactional                          // 方法开始自动开启事务
public void changePassword(...) {        // 方法结束自动 commit/rollback
    em.merge(user);
}
```

### Python
```python
async def change_password(db, user, ...):
    # 没有自动事务，全靠手动
    db.add(user)
    await db.commit()    # 手动提交
    # 抛异常则 commit 不执行，自动回滚
```

SQLAlchemy 也有上下文管理器方式（类似 `@Transactional`）：
```python
async with db.begin():   # 进入自动提交模式
    db.add(user)
    user.password = xxx
# 离开 with 块自动 commit，抛异常自动 rollback
```

---

## 总结速查表

| 你的疑问 | 答案 |
|---|---|
| `db.add(user)` 是啥？ | 等价于 `em.persist(user)` / `em.merge(user)`，把对象注册到 Session |
| 为什么要写？ | SQLAlchemy 默认不做脏检查，必须显式告诉它"这个对象要改" |
| Java 怎么不用写？ | Hibernate 自动脏检查，SQLAlchemy 要手动 |
| 事务注解呢？ | Java `@Transactional` 声明式，Python 手动 `commit()` |
| 不写 add 会怎样？ | **静默失败** —— 不报错，但不更新数据库 |
| `commit()` 干什么？ | 提交事务，把 pending 的 SQL 真正发给数据库执行 |
| `refresh()` 干什么？ | 从数据库重新读取整行，拿到自动生成的值（时间戳等） |
