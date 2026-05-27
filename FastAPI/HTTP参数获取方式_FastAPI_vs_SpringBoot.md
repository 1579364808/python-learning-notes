# HTTP 参数获取方式：FastAPI vs Spring Boot

## `Header` / `Query` / `Path` / `Body` 参数提取

### Python (FastAPI)

```python
from fastapi import Header, Query, Path, Body

async def handler(
    authorization: str = Header(..., alias="Authorization"),
    page: int = Query(1, ge=1),
    item_id: int = Path(..., ge=0),
    payload: dict = Body(...),
):
    ...
```

### Java (Spring Boot)

```java
public ResponseEntity<?> handler(
    @RequestHeader("Authorization") String authorization,
    @RequestParam(defaultValue = "1") @Min(1) int page,
    @PathVariable @Min(0) int item_id,
    @RequestBody Map<String, Object> payload
) {
    ...
}
```

### 差异表格

| 对比项 | Python (FastAPI) | Java (Spring) |
|--------|------------------|---------------|
| 声明位置 | 函数参数类型注解，特殊默认值 | 方法参数上的注解 |
| HTTP头提取 | `Header(...)` 作默认值 | `@RequestHeader` |
| 查询参数提取 | `Query(...)` 作默认值 | `@RequestParam` |
| 路径变量提取 | `Path(...)` 作默认值 | `@PathVariable` |
| 请求体提取 | `Body(...)` 作默认值 | `@RequestBody` |
| 别名映射 | `alias="Authorization"` | `@RequestHeader("Authorization")` 直接写名称 |
| 必填标记 | `...` (Ellipsis) 表示必填 | 默认必填，`required=false` 可选 |
| 校验 | 参数传入 `Query(ge=1)` 等 | Javax/Jakarta Validation 注解 `@Min` |
| 默认值 | 传给 `Query(1)` 的第一个参数 | `defaultValue = "1"` |

### 要点说明

1. **`...` (Ellipsis) 的含义**：在 Python 中 `...` 是 Ellipsis 字面量，Pydantic/FastAPI 用它表示"该字段必填且无默认值"。等价于 Java 中不给 `defaultValue`。

2. **`alias` 的作用**：Python 变量名不能包含大写字母开头的标准 HTTP 头名（如 `Authorization`），所以变量用小写 `authorization`，用 `alias="Authorization"` 映射到真实头名。不加 alias 则会匹配小写的 `authorization` 头。

3. **特殊默认值机制**：`Header()` 是一个函数调用，返回一个特殊对象作为参数默认值。FastAPI 通过检查参数默认值是否是 `Header` 实例来判断参数来源（头/查询/路径/体），而不是真的把这个对象当成默认值使用。这是 Python"鸭子类型"和"可调用对象"的典型应用。

4. **Pydantic Field 一致性**：`Header()`、`Query()`、`Path()` 等本质上是 Pydantic 的 `Field()` 的别名，都支持 `alias`、`ge`、`le`、`regex` 等参数。

---

## 响应格式：FastAPI vs Spring Boot

### 最简返回

```python
# FastAPI：直接返回字典或 Pydantic 模型
@app.get("/user")
def get_user():
    return {"id": 1, "name": "Alice"}       # FastAPI 自动序列化为 JSON
```

```java
// Spring Boot：@RestController 自动序列化
@RestController
public class UserController {
    @GetMapping("/user")
    public Map<String, Object> getUser() {
        return Map.of("id", 1, "name", "Alice");  // Spring 自动序列化为 JSON
    }
}
```

**本质相同**：框架帮你做了 `对象 → JSON 字符串 + 设置 Content-Type: application/json`。

### 控制状态码

```python
# FastAPI
from fastapi import status
from fastapi.responses import JSONResponse

@app.post("/users", status_code=201)       # 方式一：装饰器参数
def create_user(...):
    return {"id": 1}

@app.post("/users")
def create_user(...):
    return JSONResponse(                     # 方式二：显式构造
        content={"id": 1},
        status_code=status.HTTP_201_CREATED
    )
```

```java
// Spring Boot
@PostMapping("/users")
@ResponseStatus(HttpStatus.CREATED)          // 方式一：注解
public Map<String, Object> createUser() {
    return Map.of("id", 1);
}

@PostMapping("/users")
public ResponseEntity<Map<String, Object>> createUser() {  // 方式二：ResponseEntity
    return ResponseEntity
        .status(HttpStatus.CREATED)
        .body(Map.of("id", 1));
}
```

| 对比 | FastAPI | Spring Boot |
|------|---------|-------------|
| 装饰器/注解设置状态码 | `status_code=201` | `@ResponseStatus(HttpStatus.CREATED)` |
| 灵活控制 | `JSONResponse(content=..., status_code=...)` | `ResponseEntity.status(...).body(...)` |
| 错误响应 | `raise HTTPException(status_code=404)` | `throw new ResponseStatusException(HttpStatus.NOT_FOUND)` |

### 统一响应格式（重点：和 `统一成功响应格式.md` 对照）

你的项目里用了 `success_response` 包装了一层统一格式，Spring Boot 那边也是同样的套路：

```python
# ===== FastAPI（你的项目） =====
# 见 C:\Users\27987\Documents\python-learning-notes\FastAPI\统一成功响应格式.md

def success_response(message="success", data=None):
    content = {
        "code": 200,
        "message": message,
        "data": data,
    }
    return JSONResponse(content=jsonable_encoder(content))

# 路由中使用
@router.post("/register")
async def register(...):
    return success_response(message="注册成功", data=response_data)
```

```java
// ===== Spring Boot =====
// 通常建一个 R<T> 泛型类统一包一层

@Data
@NoArgsConstructor
@AllArgsConstructor
public class R<T> {
    private int code;
    private String message;
    private T data;

    public static <T> R<T> success(T data) {
        return new R<>(200, "success", data);
    }

    public static <T> R<T> success(String message, T data) {
        return new R<>(200, message, data);
    }
}

// 路由中使用
@PostMapping("/register")
public R<UserVO> register(@RequestBody UserRequest req) {
    User user = userService.register(req);
    UserVO vo = new UserVO(user.getId(), user.getUsername());
    return R.success("注册成功", vo);   // 和你的 success_response 一模一样
}
```

最终在网络上传输的报文完全一样：

```text
HTTP/1.1 200 OK
Content-Type: application/json

{"code": 200, "message": "注册成功", "data": {"id": 1, "username": "Alice"}}
```

**差异对比：**

| 对比项 | FastAPI（你的项目） | Spring Boot |
|--------|-------------------|-------------|
| 统一响应类 | `success_response()` 函数 | `R<T>` 泛型类 |
| 序列化特殊类型 | `jsonable_encoder()` 递归转换 | Jackson 自动处理（需配置日期格式等） |
| Pydantic ↔ Java Bean | `UserAuthResponse.model_validate(user)` | `new UserVO(user.getId(), user.getUsername())` |
| ORM 转响应对象 | `model_config = ConfigDict(from_attributes=True)` | `BeanUtils.copyProperties()` 或 MapStruct |
| 异常统一处理 | `全局异常处理器.md` 中的 `@app.exception_handler` | `@RestControllerAdvice + @ExceptionHandler` |

### 序列化对比：jsonable_encoder vs Jackson

**同一个问题，两个框架的处理方式：**

```python
# FastAPI：Python 的 datetime、UUID、Decimal 等类型不能被 json.dumps 直接序列化
# 所以你要手动调 jsonable_encoder 转成原生类型

data = {
    "created_at": datetime(2026, 5, 25, 12, 0, 0),
    "price": Decimal("19.99"),
    "user_id": UUID("550e8400-e29b-..."),
}

encoded = jsonable_encoder(data)
# → {"created_at": "2026-05-25T12:00:00", "price": 19.99, "user_id": "550e8400-..."}

JSONResponse(content=encoded)   # 再传给 JSONResponse
```

```java
// Spring Boot：Jackson 默认就能处理常见类型，但也需要配置

// 默认情况，Java 的 LocalDateTime 直接返回也会报错
@Data
public class OrderVO {
    private LocalDateTime createdAt;    // ❌ 直接返回会报错
    private BigDecimal price;            // ❌ 直接返回会报错
}

// 需要配置 Jackson 的序列化规则
@Bean
public Jackson2ObjectMapperBuilderCustomizer customizer() {
    return builder -> {
        builder.serializerByType(LocalDateTime.class, new LocalDateTimeSerializer(
            DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss")));
        builder.serializerByType(BigDecimal.class, new ToStringSerializer());
    };
}
// 或者用 application.yml 配置：
// spring.jackson.date-format = yyyy-MM-dd'T'HH:mm:ss
// spring.jackson.serialization.write-dates-as-timestamps = false

// 配置好后，直接返回就不会报错了
@GetMapping("/order")
public OrderVO getOrder() {
    return orderService.getOrder();  // Jackson 自动序列化
}
```

**区别的本质：**

| | FastAPI | Spring Boot |
|--|---------|-------------|
| 底层序列化库 | `json.dumps()`（标准库） | Jackson |
| 默认认识的特殊类型 | 只有 7 种基本类型 | 部分常见类型（如 Date），但 LocalDateTime 等仍需配置 |
| 配置方式 | 手动调 `jsonable_encoder()` 转换 | 全局配置 ObjectMapper 或加注解 `@JsonFormat` |
| 手动 vs 自动 | **显式手动转** | **隐式全局配置** |

> 延伸阅读：`统一成功响应格式.md` 第 四 节「jsonable_encoder 解决序列化问题」

### ORM 转响应对象对比：model_validate vs BeanUtils

**同一个问题：从数据库查出来的 ORM 对象，怎么转成给前端看的响应 DTO？**

```python
# ===== FastAPI（你的项目） =====

# ORM 对象（SQLAlchemy）
user = User(id=1, username="jack", password="123456")
#                    ↑ 要过滤掉！

class UserInfoResponse(BaseModel):
    id: int
    username: str
    # 没有 password，自动过滤

    model_config = ConfigDict(from_attributes=True)

# 一行转换 + 过滤
user_info = UserInfoResponse.model_validate(user)
# 自动：user_info.id = user.id
#       user_info.username = user.username
#       password 被忽略 ✅
```

```java
// ===== Spring Boot =====

// ORM 对象（JPA/Hibernate）
User user = userRepository.findById(1L).orElseThrow();
// user.getPassword() → 也要过滤掉！

public class UserVO {            // VO = Value Object，就是给前端看的
    private Long id;
    private String username;
    // 没有 password，自动过滤
}

// 方式一：手动 new 出来（最麻烦）
UserVO vo = new UserVO();
vo.setId(user.getId());
vo.setUsername(user.getUsername());
// 每个字段写一行，字段多了写死人

// 方式二：BeanUtils.copyProperties（反射，类似 model_validate）
UserVO vo = new UserVO();
BeanUtils.copyProperties(user, vo);
// 内部：遍历 UserVO 的所有字段，从 user 身上读同名字段赋值
// 同名字段自动 copy，不同名的忽略

// 方式三：MapStruct（编译期生成代码，最快）
@Mapper(componentModel = "spring")
public interface UserMapper {
    UserVO toVO(User user);
}
// MapStruct 自动生成 UserMapperImpl，编译时就把映射代码写好
```

**本质对比：**

|       | FastAPI                                 | Spring Boot                                         |
| ----- | --------------------------------------- | --------------------------------------------------- |
| 转换方法  | `PydanticModel.model_validate(orm_obj)` | `BeanUtils.copyProperties(vo, orm_obj)` 或 MapStruct |
| 字段过滤  | 只保留 Pydantic 模型中声明的字段                   | 只保留 VO 类中声明的字段                                      |
| 同名字段  | 自动匹配（大小写敏感）                             | 自动匹配（大小写敏感）                                         |
| 不同名字段 | 需 `alias` 或新增字段                         | 需 `@Mapping`（MapStruct）或手动 set                      |
| 类型转换  | Pydantic 自动做（str→int、int→float 等）       | 基本类型自动转，复杂类型需自定义转换器                                 |
| 性能    | 运行时反射                                   | BeanUtils 运行时反射 / MapStruct 编译期生成代码（快）              |

**简单记：两个框架做的是一模一样的事情——把数据库对象「过滤+转换」成响应对象。** 只不过 FastAPI 靠 Pydantic 的 `model_validate`，Spring Boot 靠 `BeanUtils.copyProperties` 或 MapStruct。

### 统一异常处理对比

```python
# FastAPI 全局异常处理
# 见 C:\Users\27987\Documents\python-learning-notes\FastAPI\全局异常处理器.md
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "message": exc.detail, "data": None}
    )
```

```java
// Spring Boot 全局异常处理
@RestControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(ResponseStatusException.class)
    public R<Void> handleResponseStatus(ResponseStatusException e) {
        return new R<>(e.getStatusCode().value(), e.getReason(), null);
    }
}
```

两者的思路完全一致：**定义一个全局拦截器，捕获异常后包装成统一的 `{code, message, data}` 格式返回**。区别只在于语言语法的不同。
