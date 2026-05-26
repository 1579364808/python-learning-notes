# passlib 密码哈希 (bcrypt)

## 背景：为什么需要这套东西？

### 灾难现场：明文存密码

```
users 表
id | username | password
1  | admin    | 123456       ← 明文！！！
```

- 数据库被拖库（SQL 注入、黑客入侵），所有密码直接暴露
- 员工内部可以查到所有人的密码
- 用户通常在不同网站用相同密码，一个泄露等于全网沦陷

### 第一代方案：MD5 哈希

```
password = md5("123456")
→ "e10adc3949ba59abbe56e057f20f883e"
```

- 问题是：**相同密码产生相同哈希值**
- 黑客可以提前算好一个"彩虹表"（常见密码 → MD5 的映射），反向查回明文
- MD5 计算极快，现代 GPU 每秒可算百亿次，暴力破解轻而易举

### 第二代方案：MD5 + 固定盐

```
password = md5("123456" + "my_app_salt")
```

- 加了固定盐，彩虹表失效了
- 但 **所有用户共用同一个盐**，如果盐泄露，依然可以批量破解

### 第三代方案（主流）：随机盐 + 慢哈希

```
password = bcrypt("123456" + 随机盐)
```

- **每个用户都有自己的随机盐**，盐存哈希结果里，不需要单独维护
- **故意设计得很慢**（单次校验几十毫秒），黑客暴力破解的成本提高百亿倍
- **业界公认标准**：bcrypt 是目前后端的主流方案，Argon2 是最新推荐（但 bcrypt 依然是绝对主流）

---

## 安装

```bash
pip install "passlib[bcrypt]"
```

---

## 主流程：注册 / 登录

```
注册: 明文密码 → hash() → 哈希值 → 存入数据库
登录: 明文密码 + 数据库哈希值 → verify() → True/False
```

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_hash_password(password: str) -> str:
    """加密：明文 -> 哈希值"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证：明文 + 哈希值 -> 是否匹配"""
    return pwd_context.verify(plain_password, hashed_password)
```

### 注册接口里的用法

```python
hashed = get_hash_password(user_input.password)  # 加密
db_user = User(hashed_password=hashed)            # 存哈希，不存明文
```

### 登录接口里的用法

```python
if not verify_password(user_input.password, db_user.hashed_password):
    raise HTTPException(status_code=401, detail="密码错误")
# 登录成功，签发 JWT Token...
```

---

## 主流方案的核心原理

### 1. 自动加盐（bcrypt 内置，无需手动处理）

bcrypt 的哈希值本身**包含盐**：

```
$2b$12$KxhfGhjfGhjfGhjfGhjfGuFGHJfGhjfGhjfGhjfGhjfGhjfGhjfGhj
│   │   │
│   │   └─ 哈希值（含盐）
│   └───── 盐
└──────── 版本 + 轮数
```

- 验证时：passlib 自动从哈希值里提取盐 → 对明文+盐重新计算 → 比较
- 开发者**不需要手动管理盐**，盐就嵌在哈希结果里

### 2. "慢"是 bcrypt 的核心安全特性

| 算法 | 每秒可破解次数 | 安全性 |
|------|--------------|--------|
| MD5 | 百亿次 | 秒破 |
| SHA-256 | 十亿次 | 能破 |
| bcrypt(rounds=12) | 几十次 | 安全 |

- `rounds`（轮数）决定计算强度，`$2b$12$` 表示 2^12 = 4096 轮迭代
- 每多 1 轮，计算时间翻倍
- passlib 默认 rounds=12，单次校验约 50-80ms
- 对用户来说慢 80ms 没感觉，但黑客暴力破解 1 亿个密码就要 **80ms × 1亿 ≈ 93天**

### 3. deprecated="auto" 的作用

```python
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
```

- 假设未来 bcrypt 被发现有漏洞，你把 schemes 换成 `["argon2", "bcrypt"]`
- 新注册的用户用 Argon2
- 老用户用 bcrypt 存的密码仍能验证（`deprecated="auto"` 会自动标记为"已弃用"）
- 等所有老用户都登录过一次后，就可以彻底去掉 bcrypt
- **无缝升级，不停服**

---

## 主流做法总结

| 维度 | 主流做法 | 不推荐的做法 |
|------|---------|-------------|
| 算法 | **bcrypt**（或 Argon2） | MD5、SHA-1、SHA-256（无盐/纯哈希） |
| 加盐 | **自动加盐**（bcrypt 内置） | 固定盐、手动管理盐 |
| 哈希值长度 | **字段长度 128**（bcrypt 结果 60 字符左右） | 设置过短导致截断 |
| 库 | **passlib**（封装性好，支持多种算法） | 自己手写哈希 |
| 验证时机 | **登录时验证** | 永远不要反解哈希（不可能） |
| 密钥管理 | **环境变量 /.env 文件** | 硬编码在代码里 |

---

## 常见问题

### bcrypt 每次哈希结果不同，怎么验证？

```
第一次 hash("123456") → "$2b$12$A...X"  （盐是 A...）
第二次 hash("123456") → "$2b$12$B...Y"  （盐是 B...，结果不同）

verify("123456", "$2b$12$A...X")
  → 从 "$2b$12$A...X" 中提取盐 A...
  → 对 "123456" + 盐 A... 重新计算
  → 比较结果是否等于 "$2b$12$A...X"
  → ✅ 匹配
```

### 怎么升级到更好的算法？

```python
# 旧配置
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 升级后：新用户用 argon2，旧用户继续用 bcrypt
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],  # 优先用 argon2
    deprecated="auto"              # bcrypt 自动被标记为 deprecated
)
```

验证时如果发现用户用的是旧算法，可以顺便更新数据库。

### 为什么不直接 pip install bcrypt？

可以，但 passlib 提供了：
- 统一 API：切换算法只需改一行 `schemes`
- 平滑迁移：`deprecated="auto"` 支持多算法共存
- 更易维护

---

## 安全警告

### 不要硬编码密钥

```python
# ❌ 错误
SECRET_KEY = "heima-toutiao-ai-secret-key-2026"

# ✅ 正确
import os
SECRET_KEY = os.getenv("TOUTIAO_SECRET_KEY")
```

详见 `环境变量与配置文件` 相关笔记。

### 其他注意事项

- 密码字段长度：数据库设为 `String(128)`，预留足够空间
- 不要自己魔改算法，不要"叠加 MD5+bcyrpt"，安全界有共识：用标准库
- HTTPS 传输：密码等敏感信息在网络上传输时必须加密
