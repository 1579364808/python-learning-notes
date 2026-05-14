# Python 异步编程：FastAPI 入门导向版

这套笔记只服务一个目标：**看懂并正确写出 FastAPI 里的 `async def` 和 `await`**。

原则：

- 每章只解决一个问题。
- 先看代码，再解释概念。
- Java 只做一句关键类比，不硬套。
- 暂时不讲 GIL、底层 Future、uvloop、复杂线程池。

## 章节安排

| 章 | 标题 | 本章目标 |
|----|------|---------|
| 01 | 为什么 FastAPI 函数前面有 `async` | 看懂 `async def root()` 是什么 |
| 02 | `async def` 和 `def` 有什么区别 | 明白协程函数调用后不会立刻执行 |
| 03 | `await` 到底在等什么 | 明白 `await` 是"等，但不堵死服务器" |
| 04 | 串行 vs 并发 | 明白 `await a(); await b()` 和 `gather()` 的区别 |
| 05 | FastAPI 里什么时候写 `async def` | 会判断接口函数该用 `async def` 还是 `def` |
| 06 | 常见错误 | 避免 `time.sleep()`、`requests`、忘记 `await` 等坑 |

## 文档文件

```text
对比Java学习python/异步编程/
├── course-outline.md
├── chapter-01-为什么FastAPI函数前面有async.md
├── chapter-02-async-def和def有什么区别.md
├── chapter-03-await到底在等什么.md
├── chapter-04-串行vs并发.md
├── chapter-05-FastAPI里什么时候写async-def.md
└── chapter-06-常见错误.md
```

## 学习方式

每章固定结构：

```md
# 本章只解决一个问题

## 先看代码

## 你应该观察到什么

## 用 Java 类比一句话

## 现在只需要记住

## 小练习
```

## 最终完成标准

学完后你应该能回答：

- FastAPI 里为什么经常写 `async def`？
- `async def` 和普通 `def` 有什么区别？
- `await` 到底是不是阻塞？
- 为什么 `time.sleep()` 不能随便放进 `async def`？
- 什么时候应该用 `asyncio.gather()`？
