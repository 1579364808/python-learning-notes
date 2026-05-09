# typing 类型注解弃用说明

## 背景

Python 3.9+ 开始弃用 `typing` 模块中的部分大写别名，改为直接使用内置类型。

## 哪些已弃用（用内置替代）

| 弃用写法 (typing) | 替代写法 (内置) | 可用版本 |
|-------------------|----------------|---------|
| `Dict[str, int]` | `dict[str, int]` | Python 3.9+ |
| `List[int]` | `list[int]` | Python 3.9+ |
| `Tuple[int, str]` | `tuple[int, str]` | Python 3.9+ |
| `Set[int]` | `set[int]` | Python 3.9+ |
| `FrozenSet[int]` | `frozenset[int]` | Python 3.9+ |
| `Type[MyClass]` | `type[MyClass]` | Python 3.9+ |

## 哪些仍需从 typing 导入（没有内置替代）

| 类型 | 导入方式 |
|------|---------|
| `Any` | `from typing import Any` |
| `Callable` | `from typing import Callable` |
| `Optional` | `from typing import Optional` (或 `X \| None`) |
| `Union` | `from typing import Union` (或 `X \| Y`) |
| `Protocol` | `from typing import Protocol` |
| `NamedTuple` | `from typing import NamedTuple` |
| `Iterable` | `from typing import Iterable` |
| `Iterator` | `from typing import Iterator` |
| `Generator` | `from typing import Generator` |
| `TypeVar` | `from typing import TypeVar` |

## Python 3.10+ 进一步简化

可以用 `|` 替代 `Optional` 和 `Union`：

```python
# Python 3.8-3.9
from typing import Optional, Union
x: Optional[str] = None
y: Union[int, str] = 1

# Python 3.10+
x: str | None = None
y: int | str = 1
```

## Optional / Union 详解

### Optional[X]

表示 **X 或 None**，相当于 Java 的 `@Nullable` 注解。

```python
from typing import Optional

# 参数 name 可以是 str 或 None
def greet(name: Optional[str]) -> str:
    if name is None:
        return "Hello, World"
    return f"Hello, {name}"
```

注意：**Python 的 Optional 只是类型注解，运行时不会自动包装值**，这与 Java 的 `Optional<String>` 容器语义完全不同。

### Union[X, Y]

表示 **X 或 Y**，Java 没有直接等价，通常用方法重载或 `Object` 类型替代。

```python
from typing import Union

def add(a: Union[int, str], b: Union[int, str]) -> str:
    return str(a) + str(b)
```

### Python 3.10+ 简写

用 `|` 替代 `Optional` 和 `Union`：

```python
# 旧写法
x: Optional[str] = None
y: Union[int, str] = 1

# 3.10+ 新写法
x: str | None = None
y: int | str = 1
```

### 对比表

| 概念 | Python | Java |
|------|--------|------|
| 可空 | `Optional[str]` 或 `str \| None` | `@Nullable String` 或 `Optional<String>` |
| 联合 | `Union[int, str]` 或 `int \| str` | 无直接等价 |

## 最佳实践

- 如果最低支持 Python 3.9，优先用内置 `dict`/`list`/`tuple` 等
- `Any` 没有替代方案，始终从 `typing` 导入
- Python 3.10+ 优先用 `X | None` 和 `X | Y`，更简洁
