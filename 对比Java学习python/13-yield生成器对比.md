# yield 生成器对比

## 一句话定性

Python 的 `yield` 相当于 Java 里自己实现一个 `Iterator`：**函数不是一次性返回所有结果，而是每次产出一个值，下一次再从暂停的位置继续执行**。

## Python 写法

```python
def count_to_three():
    print("开始")
    yield 1
    print("继续")
    yield 2
    print("结束前")
    yield 3


gen = count_to_three()

print(next(gen))  # 开始 -> 1
print(next(gen))  # 继续 -> 2
print(next(gen))  # 结束前 -> 3
```

重点：函数里只要出现 `yield`，这个函数就不是普通函数了，而是**生成器函数**。

调用它时不会立刻执行函数体：

```python
gen = count_to_three()  # 此时不会打印"开始"
```

只有你取值时才执行：

```python
next(gen)  # 执行到第一个 yield 停住
```

## Java 对比代码

```java
import java.util.Iterator;

class CountToThree implements Iterator<Integer> {
    private int current = 1;

    @Override
    public boolean hasNext() {
        return current <= 3;
    }

    @Override
    public Integer next() {
        return current++;
    }
}

public class Main {
    public static void main(String[] args) {
        Iterator<Integer> it = new CountToThree();

        System.out.println(it.next()); // 1
        System.out.println(it.next()); // 2
        System.out.println(it.next()); // 3
    }
}
```

Python 的 `yield` 帮你省掉了 Java 里手写 `Iterator` 的状态管理。

## 最小心智模型

把 `yield` 理解成：

```text
return 一个值，但函数不结束；
下次继续从 yield 后面往下跑。
```

普通 `return`：

```python
def f():
    return 1
    return 2  # 永远执行不到
```

`yield`：

```python
def f():
    yield 1  # 第一次取值停在这里
    yield 2  # 第二次继续到这里
```

## for 循环怎么用

通常不会手动写 `next()`，而是直接 `for`：

```python
def count_to_three():
    yield 1
    yield 2
    yield 3


for num in count_to_three():
    print(num)
```

输出：

```text
1
2
3
```

`for` 循环内部其实就是不断调用 `next()`。

## 差异表格

| 对比项 | Python `yield` | Java `Iterator` |
|--------|----------------|-----------------|
| 核心作用 | 惰性地产出一个个值 | 惰性地产出一个个值 |
| 状态保存 | Python 自动保存函数执行位置 | 需要自己用字段保存状态 |
| 使用方式 | `for x in generator` | `while (it.hasNext())` |
| 结束方式 | 函数执行完自动结束 | `hasNext()` 返回 `false` |
| 代码量 | 少 | 多 |

## 要点说明

1. `yield` 不是普通返回值，它会让函数变成生成器。
2. 生成器是惰性的：你不取值，它就不执行。
3. `yield` 会暂停函数，下次取值时从暂停位置继续。
4. 大数据场景常用 `yield`，因为它不用一次性把所有数据放进内存。

---

## 进阶用法：yield 做资源管理（FastAPI 依赖注入）

### 和"遍历"是同一个原理，但用途不同

```python
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session  # 把 session 借出去
        finally:
            await session.close()
```

这里的 `yield` 不是用来"遍历数据"，而是用来**把函数切成两半**：

```text
FastAPI 收到请求
  → 调用 get_db()
    → 执行到 yield session，暂停
    → 把 session 交给接口函数用
    → 接口函数执行完
    → 从 yield 后面继续执行
    → 执行 finally 里的 close()
```

### Java 对比

```java
// Java try-with-resources
try (Session session = factory.openSession()) {
    // 用 session 干活
    // 自动调用 session.close()
}
```

```java
// Spring @Bean 的 destroyMethod
@Bean(destroyMethod = "close")
public Session session() {
    return factory.openSession();
}
```

### 差异表格

| 阶段 | Python yield | Java 对应 |
|------|-------------|-----------|
| 获取资源 | `yield` 之前的代码 | `try (...)` 里的初始化 |
| 使用资源 | 接口函数拿到 `session` | `try` 块里的业务代码 |
| 释放资源 | `yield` 之后的代码 | 自动调用 `close()` |

### 要点

- 这里的 `yield` 不是"遍历"，是**"把资源借出去，用完了再收回来"**。
- `yield` 之前的代码 = 初始化。
- `yield` 之后的代码 = 清理。
- FastAPI 会在请求结束后自动回来执行 `yield` 后面的清理代码。

### 为什么有 `async with` 还要用 `yield`

```python
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

`async with` 只管 session 的创建和关闭，但 FastAPI 需要**把 session 借给接口函数用**——`yield` 在这里负责"暂停并递出去"。

不用 `yield` 会怎样：

```python
async def get_db():
    async with AsyncSessionLocal() as session:
        return session  # ❌ 一退出 with 就关了，接口拿不到
```

```python
async def get_db():
    session = AsyncSessionLocal()  # 不关？  ❌ 资源泄漏
    return session
```

执行顺序：

```text
FastAPI → get_db()
          创建 session（async with 进入）
          遇到 yield，暂停
          把 session 给接口用
          接口执行完
          → 回到 get_db() 继续
          关闭 session（async with 退出）
```

Java 类比相当于 AOP 的 `@Around` 环绕通知：

```java
@Around("execution(* controller.*(..))")
public Object around(ProceedingJoinPoint pjp) {
    Session session = factory.openSession();   // ① async with 进入
    Object result = pjp.proceed();             // ② yield = 暂停，让接口执行
    session.close();                           // ③ async with 退出
    return result;
}
```

**一句话：`async with` 管开门关门，`yield` 管把东西递出去。**
