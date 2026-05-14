# 第 4 章：串行 vs 并发

## 本章只解决一个问题

为什么两个 `await` 写在一起，不一定是并发？

## 先看代码

先准备一个模拟请求：

```python
import asyncio


async def get_user():
    await asyncio.sleep(2)
    return "用户信息"


async def get_orders():
    await asyncio.sleep(2)
    return "订单列表"
```

串行写法：

```python
async def main():
    user = await get_user()
    orders = await get_orders()
    print(user, orders)


asyncio.run(main())
```

总耗时大约 4 秒。

## 你应该观察到什么

这两句是一个等完再等另一个：

```python
user = await get_user()
orders = await get_orders()
```

流程是：

```text
等用户 2 秒 -> 用户好了 -> 再等订单 2 秒 -> 订单好了
```

如果两个操作互相不依赖，可以并发：

```python
async def main():
    user, orders = await asyncio.gather(
        get_user(),
        get_orders(),
    )
    print(user, orders)


asyncio.run(main())
```

总耗时大约 2 秒。

流程是：

```text
同时等用户和订单 -> 谁先好都行 -> 两个都好了再继续
```

## 用 Java 类比一句话

`asyncio.gather(a(), b())` 类似 Java 里 `CompletableFuture.allOf(f1, f2)`：两个任务一起跑，最后等它们都完成。

## 现在只需要记住

- `await a(); await b()`：串行，一个完了再执行下一个。
- `await asyncio.gather(a(), b())`：并发，两个一起等。
- 如果第二步依赖第一步结果，就用串行。
- 如果两个操作互不依赖，就可以用 `gather`。

## 小练习

下面两个查询互不依赖，应该怎么写？

```python
user = await get_user()
settings = await get_settings()
```

推荐写法：

```python
user, settings = await asyncio.gather(
    get_user(),
    get_settings(),
)
```
