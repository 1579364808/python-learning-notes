# 依赖注入对比：FastAPI Depends vs Spring DI

## 一句话定性

FastAPI 的 `Depends` 相当于 Spring 的 `@Autowired` + 构造器注入，但它是**函数级别的依赖注入**，不是类级别的。

## Spring 做法

```java
@RestController
public class UserController {

    @Autowired  // 声明依赖，Spring 自动注入
    private UserService userService;

    @GetMapping("/users")
    public List<User> listUsers(
            @RequestParam int page,
            @RequestParam int size) {
        return userService.findAll(page, size);
    }
}
```

## FastAPI 做法

```python
from fastapi import Depends, FastAPI

app = FastAPI()


def common_parameters(skip: int = 0, limit: int = 100):
    return {"skip": skip, "limit": limit}


@app.get("/users/")
def list_users(commons: dict = Depends(common_parameters)):
    return {"params": commons}
```

## 差异表格

| 对比项 | Spring (Java) | FastAPI Depends (Python) |
| :--- | :--- | :--- |
| 注入目标 | 类的字段 / 构造器参数 | 函数的参数 |
| 声明方式 | `@Autowired` / 构造器参数 | `Depends(某个函数)` |
| 依赖来源 | IoC 容器管理的 Bean | 普通函数的返回值 |
| 注入时机 | 启动时创建 Bean 就注入 | 每次请求进来时执行函数 |
| 作用域 | 单例 / 原型 / 请求等 | 每次请求重新执行一次 |
| 生命周期管理 | 框架全权管理 | 你自己控制，用 `yield` 管理资源 |

## 要点说明

1. **Spring 的 DI 是"找 Bean"**：启动时扫描所有类，发现 `@Autowired` 就去容器里找匹配的 Bean 塞进来。你不需要手动调用任何东西，框架全自动。

2. **FastAPI 的 Depends 是"先执行这个函数"**：`Depends(common_parameters)` 的意思是——在进入 `list_users` 之前，先执行 `common_parameters(skip, limit)`，把返回值作为参数传给 `list_users`。本质就是函数嵌套调用，只是 FastAPI 帮你自动做了。

3. **为什么比 Spring 好理解？** Spring 的 DI 依赖"反射 + 容器 + 代理"，对新手是个黑盒。而 `Depends` 是显式的函数调用：你看到 `Depends(common_parameters)`，就知道 FastAPI 会调用 `common_parameters()` 并把结果传进来。