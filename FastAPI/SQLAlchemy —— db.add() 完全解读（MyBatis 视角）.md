# SQLAlchemy `db.add()` 完全解读

> 背景：Java Spring Boot + MyBatis → 转 Python FastAPI + SQLAlchemy

---

## 核心一句话

`db.add(user)` 的作用是：**把这个 Python 对象注册到当前数据库会话（Session），告诉 ORM"这个对象我要存/改，commit 时请生成对应的 SQL 语句"**。

如果你不写 `db.add(user)`，就算改了对象的属性，commit 也不会生成任何 SQL。

---

## MyBatis 视角：`db.add()` 到底对应什么？

### MyBatis 的写法
```java
// 1. 查出来
User user = sqlSession.selectOne("UserMapper.findById", id);

// 2. 改属性
user.setPassword(newPwd);

// 3. 显式调用 update
userMapper.updatePassword(user);   // ← 你手动指定了"我要执行 UPDATE"

// 4. 提交事务
sqlSession.commit();
```

### SQLAlchemy 的写法
```python
# 1. 查出来
user = await get_user_by_username(db, username)

# 2. 改属性
user.password = hashed_new_pwd

# 3. 告诉 ORM"这个对象我要改"
db.add(user)                        # ← 相当于告诉 ORM：请把 user 加入跟踪列表

# 4. 提交事务 —— ORM 自动对比修改前后，生成 UPDATE
await db.commit()
```

**关键区别：**
- MyBatis：你要**手动写 SQL 或调用 Mapper 方法**（`updatePassword`），明确说"执行这条 UPDATE"
- SQLAlchemy：你只需 `db.add(user)` + `commit()`，ORM **自动对比对象修改前后**，自己生成 UPDATE 语句

---

## 那为什么不加 `db.add()` 就不行？

因为 SQLAlchemy 的 Session **默认不追踪**一个对象的修改。你要主动 `db.add(obj)` 把它加入 Session 的"观察名单"，Session 才会在 commit 时对比这个对象的"旧值 vs 新值"，生成 UPDATE。

```python
user.password = "new_hash"     # 改了内存中的属性
# 忘了 db.add(user)
await db.commit()              # ✅ 不报错，但 UPDATE 没发出
# 数据库密码没变！静默失败
```

这就像 MyBatis 里你改了对象的属性，但忘了调 `userMapper.update(user)`——数据不会真正写到数据库。

---

## 对象在 Session 中的 4 种状态

| 状态 | 含义 | 怎么进来的 |
|---|---|---|
| **Transient（临时）** | 纯 Python 对象，数据库没这行 | `User(name="abc")` new 出来的 |
| **Pending（待定）** | 已 `add`，但还没 `commit` | `db.add(obj)` 之后 |
| **Persistent（持久）** | 已 `commit`，与数据库某行绑定 | `commit()` 成功后 |
| **Detached（分离）** | 曾经是 Persistent，但 Session 关了/对象传出去了 | 跨函数传递时 |

`db.add(user)` 的作用就是把对象从 **Detached → Pending**，让 Session 开始跟踪它。

---

## 新建 vs 修改：`db.add()` 分别干什么

| 场景 | 代码 | commit 时生成 |
|---|---|---|
| **新建用户** | `user = User(...)` → `db.add(user)` → `commit()` | **INSERT** |
| **修改用户** | `user = 查出来的` → 改属性 → `db.add(user)` → `commit()` | **UPDATE** （ORM 发现已有 id） |

ORM 怎么判断是 INSERT 还是 UPDATE？看**主键（id）有没有值**：
- id = None → INSERT
- id 有值 → UPDATE

---

## SQLAlchemy 的事务怎么控制？

### MyBatis
```java
@Transactional            // Spring 声明式事务
public void changePassword() {
    userMapper.updatePassword(user);
    // 方法结束自动 commit，抛异常自动 rollback
}
```
或手动：
```java
sqlSession.getConnection().setAutoCommit(false);
try {
    userMapper.updatePassword(user);
    sqlSession.commit();
} catch (Exception e) {
    sqlSession.rollback();
}
```

### SQLAlchemy
```python
# 手动模式（本项目的写法）
db.add(user)
await db.commit()        # 提交事务
# 前面任何一行抛异常 → commit 不会执行 → 自动回滚

# 上下文管理器模式（类似 @Transactional）
async with db.begin():
    db.add(user)
    user.password = xxx
    # 离开 with 块自动 commit，抛异常自动 rollback
```

没有注解，全靠手动 `commit()` 或 `async with db.begin()`。

---

## 那 `commit()` 和 `refresh()` 又是什么？

| 方法 | 对应 MyBatis 的什么 | 作用 |
|---|---|---|
| `db.commit()` | `sqlSession.commit()` | 提交事务，把 SQL 发给数据库执行 |
| `db.refresh(user)` | 重新 `selectById` 查一遍 | 从数据库重新读回整行数据，拿到**数据库自动生成的值**（自增 id、创建时间、更新时间等） |

**为什么要 refresh？**
```python
user = User(username="张三", password="xxx")
db.add(user)
await db.commit()
# 此时 user.id 有值了（SQLAlchemy 自动取回了自增 id）
# 但 user.create_at 还是 None（这是数据库 DEFAULT 生成的，Python 对象不知道）
await db.refresh(user)
# 现在 user.create_at 有值了
```

---

## 总结速查表（MyBatis 对比）

| 问题 | 答案 |
|---|---|
| `db.add(user)` 是干嘛的？ | 把对象注册到 Session，告诉 ORM"commit 时要处理这个对象" |
| 对应 MyBatis 的什么？ | 相当于你调了 `userMapper.update(user)` 之前的"注册"步骤 |
| 不加会怎样？ | **静默失败** —— 不报错，但数据库不变 |
| MyBatis 怎么不用写这个？ | MyBatis 要你**手动调 Mapper 方法**，不存在"自动追踪" |
| 事务怎么控制？ | `commit()` = `sqlSession.commit()`，没有注解 |
| 新建和修改都是 `db.add()`？ | 是的，ORM 根据 id 有没有值自动判断 INSERT 还是 UPDATE |
| 为什么要 `refresh()`？ | 相当于重新 `selectById`，拿到数据库自动生成的时间戳等字段 |
