# model_dump(exclude_unset, exclude_none) 对比 Java MyBatis 动态 SQL

## 场景

用户只传了部分字段（如只改昵称），后端只更新传了的字段，不覆盖其他字段为 NULL。

## Python vs Java 代码对比

### Python（Pydantic + SQLAlchemy）

```python
# 客户端传来: {"nickname": "新昵称"}
# user_data 是 UserUpdateRequest Pydantic 模型

update(User).where(User.username == "xx").values(
    **user_data.model_dump(exclude_unset=True, exclude_none=True)
)
# 自动生成: UPDATE user SET nickname='新昵称' WHERE username='xx'
```

### Java（MyBatis）

```xml
<update id="updateUser" parameterType="UserDTO">
    UPDATE user
    <set>
        <if test="nickname != null"> nickname = #{nickname}, </if>
        <if test="avatar != null"> avatar = #{avatar}, </if>
        <if test="gender != null"> gender = #{gender}, </if>
        <if test="bio != null"> bio = #{bio}, </if>
        <if test="phone != null"> phone = #{phone}, </if>
    </set>
    WHERE username = #{username}
</update>
```

## 差异表格

| 对比项          | Python (Pydantic)                                        | Java (MyBatis)                  |
| ------------ | -------------------------------------------------------- | ------------------------------- |
| 只更新非空字段      | `model_dump(exclude_unset=True, exclude_none=True)` 自动过滤 | 每个字段手写 `<if test="xx != null">` |
| 解包到 SQL 参数   | `**dict` 直接解包到 `.values()`                               | 手动组装 SET 子句                     |
| 判断客户端是否发了该字段 | `exclude_unset` 原生支持                                     | 无对应机制，只能用 null 近似判断             |
| 新增字段的影响      | 自动纳入（只要 Pydantic 模型加了字段）                                 | 需新增 `<if>` 标签                   |

## 要点说明

1. **`exclude_unset=True`** — 只保留客户端 **显式发送** 的字段。比如客户端只传 `{"nickname":"xx"}`，即使模型还有 `avatar/gender/bio`，也不会出现在字典里。
2. **`exclude_none=True`** — 过滤掉值为 `None` 的字段。与 `exclude_unset` 一起用 = "客户端发了 **且** 值不为 null 的字段"。
3. **`**dict` 解包** — Python 语法，`f(**{"a":1, "b":2})` 等价于 `f(a=1, b=2)`。这里把字典展开为 SQLAlchemy `.values()` 的命名参数。
4. **Java 的局限** — Java 没有字典解包语法，每个字段必须手写 `<if>`。如果要判断"客户端是否发了这个字段"，还需要额外的标记字段（如 `isSet_nickname`），非常繁琐。
