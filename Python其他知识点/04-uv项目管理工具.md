# uv 项目管理工具

## 一句话总结

**uv** 是 Astral 公司（就是搞 Ruff 那个）用 Rust 写的极速 Python 包管理器，可以替代 `pip` + `pip-tools` + `pipx` + `poetry` + `pyenv` + `virtualenv` 等一系列工具。

---

## 安装 uv

```powershell
# PowerShell (winget)
winget install --id=astral-sh.uv

# PowerShell (官方脚本，推荐)
powershell -ExecutionPolicy RemoteSigned -c "irm https://astral.sh/uv/install.ps1 | iex"

# 或直接下载 exe 放到 PATH 里
```

验证安装：

```powershell
uv --version
```

升级 uv：

```powershell
uv self update
```

---

## 核心概念

### 项目（Project）与 pyproject.toml 详解

项目 = 一个由 `pyproject.toml` 描述的 Python 代码集合。这个文件是**项目的身份证 + 购物清单 + 说明书**。

#### 为什么会有 pyproject.toml？

在 2016 年之前，Python 项目元数据分散在多个文件中：

- `setup.py` — 可执行脚本，定义包信息（但不标准，可以写任意代码）
- `setup.cfg` — 静态配置文件（可选）
- `requirements.txt` — 依赖列表（纯文本，无标准格式）
- `MANIFEST.in` — 打包时要包含哪些额外文件
- `Pipfile` / `Pipfile.lock` — pipenv 用的（非标准）

社区痛点了：**太碎片化了**。所以 PEP 518 / PEP 621 统一了标准，用 `pyproject.toml` 一个文件搞定所有元数据。`toml` 格式比 `ini` 更强（支持嵌套、数组、多级表），比 `yaml` 更简单明确。

#### uv init 生成的真实 pyproject.toml 逐行解析

执行 `uv init my-project` 后，项目根目录下会生成一个 `pyproject.toml`。下面是一个更完整的例子（添加了依赖后），逐行注释：

```toml
# pyproject.toml — 项目说明书
# 格式是 TOML，用 [section] 分块，key = value

# ───────── [project] 块：项目身份证 ─────────
# PEP 621 标准定义的核心字段，任何 Python 工具都能读懂
[project]
name = "my-project"              # 项目名，PyPI 发布时也用这个名字
version = "0.1.0"                # 语义化版本
description = "Add your description here"  # 简短描述
readme = "README.md"             # 指向项目说明文档
requires-python = ">=3.12"       # 项目需要的最低 Python 版本
authors = [
    { name = "Your Name", email = "you@example.com" },
]                                # 作者列表（数组套表）

# ─── 依赖声明（核心中的核心） ───
# uv add requests 会自动在这行下面追加
dependencies = [
    "fastapi>=0.100.0",
    "uvicorn[standard]>=0.20.0",
    "requests>=2.28",
]

# ─── 可选依赖（extras） ───
# uv add --optional database psycopg 会生成这块
[project.optional-dependencies]
database = [
    "psycopg[binary]>=3.1",
]
cli = [
    "rich>=13.0",
]

# ───────── [dependency-groups] 块：依赖分组 ─────────
# PEP 735 标准，替代 poetry 的 [tool.poetry.group.dev]
# uv add --dev pytest 等效于 uv add --group dev pytest
[dependency-groups]
dev = [
    "pytest>=8.0",
    "ruff>=0.4.0",
]
lint = [
    "ruff>=0.4.0",
]

# ───────── [project.urls] 块：项目链接 ─────────
[project.urls]
Homepage = "https://example.com"
Documentation = "https://example.com/docs"
Source = "https://github.com/you/my-project"
Issues = "https://github.com/you/my-project/issues"

# ───────── [build-system] 块：构建工具配置 ─────────
# 告诉 pip / uv 怎么把这个项目打包成 .whl / .tar.gz
[build-system]
requires = ["hatchling"]   # 构建时需要安装 hatchling
build-backend = "hatchling.build"  # 使用 hatchling 作为构建后端

# ───────── [tool.uv] 块：uv 专属配置 ─────────
# 只对 uv 生效，其他工具忽略
[tool.uv]
package = true             # 是否构建为可分发包
dev-dependencies = []      # 旧写法，现在推荐用 [dependency-groups]

# ───────── [tool.ruff] / [tool.pytest] 等 ─────────
# 其他工具的配置也写在这个文件里，各自认领自己的块
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

#### 各块速查

| 块（Section） | 必须？ | 作用 | 由谁管理 |
|--------------|--------|------|---------|
| `[project]` | **是** | 项目元数据 + 核心依赖 | 手动 + `uv add` |
| `[project.optional-dependencies]` | 否 | 可选依赖（extras） | `uv add --optional` |
| `[dependency-groups]` | 否 | 开发/测试等分组依赖 | `uv add --dev` / `--group` |
| `[project.urls]` | 否 | 项目链接 | 手动 |
| `[build-system]` | **是** | 构建后端（打包工具） | `uv init --build-backend` |
| `[tool.uv]` | 否 | uv 专属配置 | 手动 |
| `[tool.xxx]` | 否 | 其他工具配置 | 各自工具管理 |

#### 应用项目（app） vs 库项目（lib/package）—— 彻底讲透

这个问题没讲清楚是我的问题。我们换个思路，直接从「**Python 怎么找到你的代码**」这个根本问题出发。

##### 先看一个具体问题：为什么 app 项目不能 `pip install`？

假设你建了两个项目：

```powershell
# ─── 项目 A：默认 app ───
uv init project-a
cd project-a
```

生成的 `project-a/pyproject.toml`：

```toml
[project]
name = "project-a"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["requests"]
```

然后执行：

```powershell
# 项目 A 目录下可以这么运行
uv run python hello.py     # ✅ 能运行
pip install -e .           # ❌ 报错：No `[build-system]` in pyproject.toml

# 跑到别的目录里，想 import project-a？
cd ..
python -c "import project_a"   # ❌ ModuleNotFoundError
```

```powershell
# ─── 项目 B：用 --lib ───
uv init --lib project-b
cd project-b
```

生成的 `project-b/pyproject.toml`：

```toml
[project]
name = "project-b"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["requests"]

[build-system]                         # 多了这个！
requires = ["hatchling"]
build-backend = "hatchling.build"
```

然后执行：

```powershell
uv run python -c "import project_b"    # ✅ 可以 import 自己
pip install -e .                       # ✅ 能安装
cd ..
python -c "import project_b"           # ✅ 安装后就能随处 import 了
```

##### 核心差异就一句话

| | app 模式 | lib 模式 |
|--|---------|---------|
| 有没有 `[build-system]` | **没有** | **有** |
| `pip install -e .` 能不能装 | ❌ 不能 | ✅ 能 |
| 别人能不能 `import` 你的代码 | ❌ 不能 | ✅ 能（先 pip install） |
| 能不能发布到 PyPI | ❌ 不能 | ✅ 能 |
| 能不能直接运行脚本 | ✅ 能（uv run hello.py） | ✅ 能 |
| 目录结构 | 扁平（`hello.py`） | `src/<包名>/` | 

**app 模式的本质**：你的代码就是**原地执行**的脚本文件，Python 直接从当前目录找到它并运行。不需要安装，不需要打包。

**lib 模式的本质**：你的代码是一个**需要被安装的包**，安装后才能被 `import`。`[build-system]` 就是告诉 pip/uv：「请按这个流程把我打包并安装到环境里」。

##### 与 Java 对照

Java 没有这个区分，因为 **Maven 总是把所有项目打成 JAR**，区别只是一个 JAR 有没有 `main()` 方法。

Python 不同，因为：

- Python 可以直接运行一个 `.py` 文件：`python hello.py` → 不需要安装，不需要打包
- Python 也可以 `pip install` 一个包，然后 `import` 它 → 需要打包和安装
- **这两种用法都是 Python 的主流用法**，所以工具需要你告诉它：你是哪种？

##### 真实决策树

```
你要写代码做什么？
├── 自己运行（Web 服务、脚本、AI 实验、数据分析）
│   └── → 用 app 模式（uv init）
│
├── 发布给别人用（工具库、SDK、框架、通用组件）
│   └── → 用 lib 模式（uv init --lib）
│
└── 写一个 CLI 工具，即要自己用也要发布
    └── → 用 --package（uv init --package）
```

##### 再举几个具体例子

| 真实场景 | 选哪个 | 为什么 |
|---------|-------|-------|
| 你写一个 FastAPI 博客后端，自己部署运行 | app | 你的代码只是跑在服务器上，没人会 `pip install` 你的博客 |
| 你写一个 pandas 辅助函数库，分享给同事 | lib | 同事要 `pip install` 它，然后 `from your_lib import ...` |
| 你写一个 `mycli` 命令行工具，要发布到 PyPI | package | 既是可运行的 CLI，也要能被 `pip install mycli` |
| 你用 Jupyter Notebook 做数据分析 | app | 不需要打包，写着玩的 |
| 你写一个 Django 项目 | app | Django 项目本身就是一个 Web 应用，不是库 |
| 你写 django-rest-framework 这样的插件 | lib | 别人要在 Django 项目里 `pip install` 它 |

##### 那 --lib 和 --package 又有什么区别？

几乎没区别。唯一的区别是**谁帮你打包**：

```toml
# --lib：用 hatchling 打包
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

# --package：用 uv 自带的打包工具
[build-system]
requires = ["uv"]
build-backend = "uv"
```

效果完全一样。新手随便选一个，推荐 `--lib`。

#### 手动编辑 vs 命令操作

**推荐用命令**，因为 `uv add` / `uv remove` 会自动：

1. 修改 `[project].dependencies` 或 `[dependency-groups]`
2. 重新解析依赖树
3. 更新 `uv.lock`
4. 同步 `.venv`

**手动改 pyproject.toml 后**需要自己执行 `uv lock && uv sync`。

#### 常见问题

**Q: 为什么有两个地方写依赖？`dependencies` 和 `[dependency-groups]` 有什么区别？**

`[project].dependencies` = **运行时必须的**依赖，别人 `pip install` 你的包时会装这些。

`[dependency-groups]` = **开发时用的**依赖（测试、lint 等），别人安装你的包时**不会**装这些。

**Q: 没有 lock 文件会怎样？**

`uv sync` 会自动生成 `uv.lock`。如果没有 `uv.lock`，uv 会根据 `pyproject.toml` 重新解析并生成一个。

**Q: `pyproject.toml` 和 `requirements.txt` 能共存吗？**

能，但不要混用。选一个项目模式（pyproject.toml）或临时脚本模式（requirements.txt）。uv 鼓励只用 `pyproject.toml`。

### 锁文件（Lockfile）

`uv.lock` — 记录所有依赖的精确版本、哈希值、来源，保证可复现。**自动生成，不要手动编辑**。

### 虚拟环境（Virtual Environment）

uv 为每个项目在项目目录下创建一个 `.venv` 文件夹，与项目绑定。

---

## 项目管理全流程（从零开始）

### 1. 创建新项目

```powershell
uv init my-project
cd my-project
```

这会生成：

```
my-project/
  pyproject.toml   # 项目元数据 + 依赖声明
  .python-version  # 锁定的 Python 版本
  README.md
  src/
    my_project/
      __init__.py     # 仅 --lib 或 --package 模式
      py.typed        # 仅 --lib 或 --package 模式
  hello.py         # 仅默认（--app）模式
```

| 选项 | 能不能 `pip install` | 能不能发布到 PyPI | 目录结构 |
|------|---------------------|-------------------|---------|
| `uv init`（默认 app） | ❌ 不能 | ❌ 不能 | `hello.py` |
| `uv init --app` | ❌ 不能 | ❌ 不能 | `hello.py` |
| `uv init --lib` | ✅ 能 | ✅ 能 | `src/<包名>/` |
| `uv init --package` | ✅ 能 | ✅ 能 | `src/<包名>/` |
| `uv init --script` | 单文件，无项目 | 单文件，无项目 | 一个 `.py` 文件 |
| `uv init --bare` | ❌ 不能 | ❌ 不能 | 只有 `pyproject.toml` |
| `uv init --build-backend hatch` | 跟 --lib 一样 | 跟 --lib 一样 | 跟 --lib 一样 |
| `uv init --no-readme` | — | — | 不生成 README.md |
| `uv init --no-pin-python` | — | — | 不生成 `.python-version` |
| `uv init --vcs none` | — | — | 不初始化 git |

### 2. 添加依赖

```powershell
# 添加普通依赖
uv add requests

# 添加多个依赖
uv add fastapi uvicorn[standard]

# 添加指定版本
uv add "pydantic>=2.0"

# 从 Git 仓库添加
uv add "git+https://github.com/encode/httpx"

# 从本地路径添加
uv add --editable ../my-lib
```

`uv add` 会自动：
1. 更新 `pyproject.toml` 中的 `[project.dependencies]`
2. 更新 `uv.lock` 锁文件
3. 同步 `.venv` 虚拟环境（相当于自动执行 `uv sync`）

#### 版本约束写法

| 写法 | 含义 |
|------|------|
| `requests` | 任意版本 |
| `requests>=2.28` | 大于等于 |
| `requests>=2.28,<3` | 范围约束 |
| `requests==2.31.0` | 精确版本 |
| `requests~=2.28` | 兼容版本（>=2.28, <3） |
| `requests>=2.28,!=2.30.0` | 排除特定版本 |

#### 添加开发依赖

```powershell
uv add --dev pytest ruff mypy
```

这将写入 `[dependency-groups]` 中的 `dev` 组。

#### 添加可选依赖（extras）

```powershell
uv add --optional database psycopg[binary]
uv add --optional cli rich
```

这在 `[project.optional-dependencies]` 中创建 `database` 和 `cli` 两个 extras。

#### 添加自定义分组依赖

**先用一个真实场景说明为什么需要这个功能：**

你的项目可能有三种不同的开发需求：

| 场景   | 用的包                  | 什么时候安装         |
| ---- | -------------------- | -------------- |
| 跑测试  | pytest, pytest-cov   | 每次 CI 运行测试时    |
| 代码检查 | ruff, mypy           | 每次 CI 做 lint 时 |
| 文档构建 | mkdocs, mkdocstrings | 只有发布文档时才用      |

你当然可以把它们全扔进 `--dev`，但**浪费**：

- CI 的测试 job 不需要装 ruff、mypy → 装多了 CI 变慢
- CI 的 lint job 不需要装 pytest → 同理
- 本地开发更不需要装全部，一次 `uv sync` 可能装一堆你永远不用的包

**自定义分组就是为了解决这个问题：**

```powershell
# 把不同用途的依赖分到不同组
uv add --dev pytest pytest-cov      # 默认的 dev 组（大部分通用场景用这个就够了）
uv add --group lint ruff mypy       # 自定义组：lint
uv add --group docs mkdocs          # 自定义组：docs
```

`pyproject.toml` 里长这样：

```toml
[dependency-groups]
dev = ["pytest", "pytest-cov"]      # 默认开发组
lint = ["ruff", "mypy"]             # 自定义组
docs = ["mkdocs"]
```

然后可以按需安装：

```powershell
uv sync                              # 装所有组（dev + lint + docs）
uv sync --no-dev                     # 只装 main，一个组都不装
uv sync --only-group lint            # 只装 lint 组（不装 main、dev、docs）
uv sync --group lint --group docs    # 装 main + lint + docs（不装 dev）
uv sync --only-dev                   # 只装 dev 组
```

**在 CI 里的实际用法：**

```yaml
# GitHub Actions — lint job：只装 lint 相关
- run: uv sync --only-group lint
- run: uv run ruff check

# GitHub Actions — test job：只装 test 相关
- run: uv sync --only-group dev      # 假设 dev 组 = 测试工具
- run: uv run pytest
```

**这和 `--optional`（extras）有什么区别？**

```powershell
# --optional：别人 pip install 你的包时，选择性安装的额外功能
# 例如你的库支持两种数据库：
uv add --optional postgres psycopg    # pip install your-lib[postgres]
uv add --optional mysql pymysql       # pip install your-lib[mysql]

# --group：你自己的开发工具，不会被发布，别人安装你的包时不会装
uv add --group lint ruff              # 只有你自己开发时用
```

简单说：

| | `--group` | `--optional` |
|--|----------|-------------|
| 给谁用的 | **自己**（开发者） | **别人**（用户） |
| 发布到 PyPI | 不会发布 | 会发布，用户可 `pip install pkg[extra]` |
| 写在哪个 section | `[dependency-groups]` | `[project.optional-dependencies]` |
| 典型用途 | lint、test、docs 工具 | 可选数据库驱动、可选渲染引擎 |

**大多数时候你只需要 `--dev`**。自定义分组是等你发现 `--dev` 里装了太多不相干的包、CI 跑得太慢的时候，才需要拆分。

### 3. 移除依赖

```powershell
uv remove requests
uv remove --dev pytest
uv remove --group lint ruff
```

### 4. 升级依赖

```powershell
# 升级所有依赖
uv sync --upgrade

# 升级指定的单个包
uv sync --upgrade-package fastapi

# 升级某个分组的包
uv sync --upgrade-group dev

# 先锁定再同步
uv lock --upgrade-package fastapi
uv sync
```

### 5. 同步环境

```powershell
# 根据 lock 文件同步环境（等价于 npm ci / poetry install 的一步）
uv sync

# 不安装当前项目本身（CI 场景）
uv sync --no-install-project

# 仅安装 dev 组（不含 main）
uv sync --only-dev

# 排除 dev 组（生产环境）
uv sync --no-dev
```

`uv sync` 等于一次完成：解析依赖 → 检查 lock → 创建 .venv → 安装包。

### 6. 运行命令

```powershell
uv run python main.py
uv run pytest tests/
uv run uvicorn app:main
```

`uv run` 会自动激活项目的 `.venv`，无需手动 `venv\Scripts\activate`。

```powershell
# 也可以直接运行模块
uv run -m http.server 8000

# 带额外依赖运行（临时，不写入项目）
uv run --with pandas python script.py
```

### 7. 查看依赖树

```powershell
uv tree
```

输出类似：

```
my-project v0.1.0
├── fastapi v0.111.0
│   ├── pydantic v2.7.0
│   ├── starlette v0.37.0
│   └── typing-extensions v4.12.0
├── pytest v8.2.0 (dev)
│   └── iniconfig v2.0.0
└── ruff v0.4.0 (dev)
```

---

## Python 版本管理

uv 内置了 Python 下载安装功能，无需单独安装 pyenv。

### 查看可用的 Python 版本

```powershell
uv python list
```

### 安装指定 Python 版本

```powershell
uv python install 3.12
uv python install 3.11 3.10
```

### 为项目锁定 Python 版本

```powershell
# 创建 .python-version 文件
uv python pin 3.12
```

`uv python pin 3.12` 会在当前目录生成 `.python-version` 文件，之后 `uv sync`、`uv run` 都会自动使用该版本。

### 查找 Python 安装位置

```powershell
uv python find
uv python dir  # 查看 uv 管理的 Python 安装目录
```

---

## 依赖分组详解

### 一句话回答你的问题

> **分组依赖不是「特有的包」**，它们是在 main 依赖**之外额外添加**的包。
>
> **生产环境默认是没有的** ✅ 你这个理解完全正确。
>
> 但有一个关键细节：**`uv sync` 默认会装 `dev` 组**，所以你在本地开发时所有分组依赖都在。要排除它们需要用 `--no-dev`。

### 详细说明

先看一个完整的依赖布局：

```toml
[project]
dependencies = ["fastapi", "uvicorn", "pydantic"]   # ← 运行时必须的

[dependency-groups]
dev = ["pytest", "pytest-cov"]    # ← 只有开发/测试时用
lint = ["ruff", "mypy"]           # ← 只有代码检查时用
```

**依赖的「分层」关系：**

```
┌─────────────────────────────────────────────┐
│  生产环境（部署到服务器）                       │
│  uv sync --no-dev                            │
│  ┌───────────────────────────────────────┐  │
│  │  main 依赖                             │  │
│  │  fastapi, uvicorn, pydantic           │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  本地开发环境                                  │
│  uv sync（默认）                               │
│  ┌───────────────────────────────────────┐  │
│  │  main 依赖                             │  │
│  │  fastapi, uvicorn, pydantic           │  │
│  ├───────────────────────────────────────┤  │
│  │  dev 组                                │  │
│  │  pytest, pytest-cov                   │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  CI - lint job                               │
│  uv sync --only-group lint                   │
│  ┌───────────────────────────────────────┐  │
│  │  lint 组                               │  │
│  │  ruff, mypy                           │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

**关键点：**

1. **分组不是互斥的** — 如果 `main` 里有 `ruff`，`dev` 组里也有 `ruff`，只装一次
2. **分组里的包是「添加」，不是「替换」** — 就算你在 `dev` 组里写了 `pydantic`，它也不会替换 main 里的 `pydantic`
3. **分组依赖不会发布到 PyPI** — 别人 `pip install your-lib` 时，`[dependency-groups]` 里的东西**一个都不会装**

### 默认装哪些组

| 命令 | 装哪些 |
|------|-------|
| `uv sync`（默认） | main + **dev**（自定义组不装） |
| `uv sync --all-groups` | main + dev + 所有自定义组 |
| `uv sync --group lint --group test` | main + dev + lint + test |
| `uv sync --no-dev` | 只装 main（生产环境用这个） |
| `uv sync --only-group lint` | 只装 lint（不装 main） |
| `uv sync --only-dev` | 只装 dev（不装 main） |

### 部署命令到底用什么

假设你的 `pyproject.toml` 长这样：

```toml
[project]
dependencies = ["fastapi", "uvicorn"]

[dependency-groups]
dev = ["pytest", "ruff"]
lint = ["ruff"]
docs = ["mkdocs"]
```

现在要部署到服务器，装哪些包？

| 你的情况 | 部署命令 | 装了哪些 |
|---------|---------|---------|
| 只有 `dev`，没有自定义组 | `uv sync --no-dev` | 只装 main ✅ |
| 既有 `dev` 又有自定义组 | `uv sync --no-dev` | 只装 main ✅ |
| 你之前手动了 `--group lint` 装过自定义组 | 先 `uv sync --no-dev` 清理 | 只装 main ✅ |

**一句话：不管你有多少个自定义组，部署永远用 `uv sync --no-dev`。**

因为自定义组默认就不装，你只需要排除 `dev` 这一个默认组就够了。

---

## 工具管理（替代 pipx）

### 先搞清楚：什么是「工具」？

**工具** = 装在电脑上、从命令行直接敲名字就能跑的 Python 程序。

**你写的代码** vs **工具** 的区别：

|         | 你写的代码（项目）                      | 工具                                         |
| ------- | ------------------------------ | ------------------------------------------ |
| 怎么用     | `from my_lib import something` | `ruff check .`                             |
| 本质      | 给别人 **import** 的库              | 给别人 **运行** 的程序                             |
| 入口      | 没有 main 入口，只是定义了一些函数/类         | 有 `console_scripts` 入口点                    |
| 例子      | fastapi、requests、pandas        | ruff、black、uv、mkdocs、poetry                |
| 类比 Java | 一个 JAR 包的类库（commons-lang）      | 一个可执行 JAR（`java -jar app.jar`）或一个 shell 脚本 |

**具体例子：**

```powershell
# 「工具」—— 你运行它
ruff check .           # ruff 是个工具，你用它检查别人的代码
black script.py        # black 是个工具，你用它格式化别人的代码
mkdocs serve           # mkdocs 是个工具，你用它构建文档网站

# 「库」—— 你 import 它
import requests        # requests 是个库，你在自己的代码里调用它
from fastapi import FastAPI  # fastapi 是个库，你在自己的代码里用它
```

**那么 ruff 能不能既是库又是工具？** 可以。

```python
# ruff 也可以当库用
import ruff
from ruff import __version__

# 但在终端里，你通常直接敲
ruff check .
# 这种「在终端里直接敲名字就能运行」的程序，就是工具
```

### 为什么工具需要特殊管理？

因为安装方式不同：

```powershell
# ❌ 错误的方式：用 pip 全局安装
pip install ruff          # ruff 被装到全局 Python 的 site-packages
                          # 污染全局环境，不同项目需要的版本会打架

# ❌ 错误的方式：加到项目里
uv add --dev ruff         # ruff 被装到当前项目的 .venv
                          # 换一个项目就没有 ruff 可用了

# ✅ 推荐的方式：用 uv tool
uv tool install ruff      # ruff 被装到自己的独立小环境
                          # 所有终端都能调用 ruff，不污染任何项目
                          # 不同工具互相隔离，互不干扰
```

**`uv tool` 就是给「工具」准备的专用安装方式。** 每个工具住在自己的隔离小房间里，终端里随时能调用，不污染任何项目的依赖。

### 安装全局工具

```powershell
uv tool install ruff       # 装一次，以后在任意目录都能 ruff check .
uv tool install black      # 装一次，以后在任意目录都能 black .
uv tool install poe        # poe 是一个任务运行器
```

装完后在任意终端、任意目录都能直接调用：

```powershell
cd C:\Users\some-other-project
ruff check .               # ✅ 能用，因为 ruff 被 uv tool 全局注册了
black script.py            # ✅ 能用
```

### 临时运行工具（用完即走）

如果你只是偶尔用一次，不想永久安装：

```powershell
uv tool run black script.py   # 临时下载并运行 black，用完自动清理
uvx black script.py           # 简写，效果同上
```

`uvx` 就是 `uv tool run` 的简写，类比 Node.js 的 `npx`。

### 查看、升级、卸载

```powershell
uv tool list              # 查看已安装的工具列表
uv tool upgrade ruff      # 升级某个工具
uv tool uninstall ruff    # 卸载
```

---

## 脚本支持（PEP 723 内联元数据）

uv 支持在 Python 脚本顶部直接声明依赖，无需创建项目。

```python
# /// script
# dependencies = [
#   "requests>=2.28",
#   "rich",
# ]
# ///

import requests
from rich.pretty import pprint

resp = requests.get("https://api.github.com")
pprint(resp.json())
```

运行：

```powershell
uv run script.py
# 或
uv run --script script.py
```

uv 会自动创建临时环境安装依赖并执行脚本，**无需 `pyproject.toml`**。

### 创建脚本骨架

```powershell
uv init --script myscript.py
```

---

## 版本管理

### 为什么需要管版本？

当你发布一个库给别人用的时候，版本号是**你跟用户之间的通信信号**：

```text
my-lib 1.2.3 → 1.2.4
              ↑     ↑
              |     └─ patch：修了个 bug，你的代码不用改
              |
              └─────── minor：加了新功能，你的代码不用改

my-lib 1.2.3 → 2.0.0
              ↑
              └─ major：不兼容的改动，你的代码可能要改
```

这叫**语义化版本**（semver），格式就是 `MAJOR.MINOR.PATCH`：

| 段 | 什么时候加1 | 例子 | 对用户的影响 |
|----|------------|------|------------|
| **MAJOR** | 做了不兼容的 API 改动 | `1.x.x → 2.0.0` | 升级可能要改代码 |
| **MINOR** | 加了新功能，向后兼容 | `1.0.x → 1.1.0` | 升级是安全的 |
| **PATCH** | 修了 bug，向后兼容 | `1.0.0 → 1.0.1` | 升级是安全的 |

**对于应用项目（app）**：你根本不需要管版本号，因为你不会发布给别人用。

**对于库项目（lib/package）**：每次发布到 PyPI 前都要更新版本号，否则 PyPI 会拒绝（因为同名版本已存在）。

### uv version 命令

```powershell
# 查看项目当前版本
uv version

# 只输出版本号（不带项目名），给脚本用
uv version --short

# ─── 自动升级版本号 ───
uv version --bump patch   # 0.1.0 → 0.1.1（修了个 bug）
uv version --bump minor   # 0.1.0 → 0.2.0（加了新功能）
uv version --bump major   # 0.1.0 → 1.0.0（大改动，不兼容）

# ─── 手动指定版本号 ───
uv version "2.0.0"

# ─── 只看看改完会变成什么，不改文件 ───
uv version --bump minor --dry-run
```

这些命令会自动修改 `pyproject.toml` 里的 `version = "x.y.z"`，不需要你手动编辑文件。

---

## 导出 lock 文件

### 为什么需要导出？

uv 自己的锁文件是 `uv.lock`，但**不是所有工具都认识它**：

```text
你本地开发
uv sync                    ← uv 读 uv.lock，完美
```

```text
Docker 构建
FROM python:3.12
COPY requirements.txt .    ← Docker 不认识 uv.lock！
RUN pip install -r requirements.txt
```

```text
第三方安全扫描
safety check -r requirements.txt   ← 扫描工具不认识 uv.lock！
```

```text
同事还没用 uv
pip install -r requirements.txt    ← 他只装了 pip，没有 uv
```

所以 `uv export` 的作用就是：**把 uv.lock 转成 pip 能读的 requirements.txt 格式**。

### 使用示例

```powershell
# 导出完整的依赖列表（包含所有间接依赖，精确到版本号）
uv export --format requirements.txt -o requirements.txt
```
导出的文件长这样：

```text
# This file was autogenerated by uv via `uv export`.
fastapi==0.111.0
pydantic==2.7.0
starlette==0.37.0
typing-extensions==4.12.0
uvicorn==0.29.0
# ... 所有间接依赖都在这里，版本号都锁死了
```

```powershell
# 生产环境导出（排除 dev 和自定义组）
uv export --no-dev -o requirements-prod.txt

# 不输出哈希注释（某些旧 pip 版本不识别）
uv export --no-hashes -o requirements.txt
```

---

## 项目构建与发布

### 先搞清楚：什么是「构建」？

你写的代码是一堆 `.py` 文件：

```text
my-lib/
  pyproject.toml
  src/
    my_lib/
      __init__.py    # 里面写了各种函数
      utils.py
```

**本地运行**时，Python 直接从这些 `.py` 文件读取代码，不需要任何额外步骤。

**但你要把这个库发给别人用**（发布到 PyPI 让全世界 `pip install`），就需要**打包**成一个标准格式的分发文件。这个打包过程就叫**构建（build）**。

类比 Java：

| 步骤 | Java | Python |
|------|------|--------|
| 原始代码 | `.java` 源文件 | `.py` 源文件 |
| **构建** | `mvn package` | `uv build` |
| 构建产物 | `.jar` 文件 | `.tar.gz` + `.whl` 文件 |
| **发布** | `mvn deploy` 到 Maven Central | `uv publish` 到 PyPI |
| 别人使用 | 在 pom.xml 里加 dependency | `pip install my-lib` |

### uv build 生成了什么？

```powershell
uv build
```

输出：

```text
dist/
  my_lib-0.1.0.tar.gz      # 源码分发包（sdist）
  my_lib-0.1.0-py3-none-any.whl  # wheel 分发包
```

**两个文件的区别：**

| 文件 | 名字 | 装的是什么 | 什么时候用 |
|------|------|-----------|-----------|
| `.tar.gz` | sdist（source distribution） | 你的**源代码** | 当 PyPI 上没有对应平台的 wheel 时，pip 下载这个然后在用户机器上编译 |
| `.whl` | wheel（built distribution） | 已经**打包好**的代码，直接解压就能用 | 大多数情况，pip 优先用这个，**安装更快** |

简单理解：
- **sdist**（`.tar.gz`）= 发给你源码，你自己编译安装
- **wheel**（`.whl`）= 发给你一个已经「编译好」的包，pip 下载后直接解压就能用

对于纯 Python 项目（不涉及 C 扩展），wheel 其实和源码没区别，只是格式不同。wheel 被优先使用因为它安装更快。

### uv publish 是干什么的？

```powershell
uv publish
```

把刚才 `dist/` 目录下生成的两个文件**上传到 PyPI**（Python Package Index，相当于 Java 的 Maven Central）。

上传之后，全世界的人就可以：

```powershell
pip install my-lib          # 从 PyPI 下载安装你的库
```

**这就是「发布」的全部含义**。

### 前置条件

只有**库项目（--lib / --package）**才能构建和发布。应用项目（默认的 --app）没有 `[build-system]`，不能构建。

发布到 PyPI 前需要：

1. 注册 PyPI 账号（https://pypi.org）
2. 生成一个 API token
3. 设置环境变量：

```powershell
# 方式一：API token（推荐）
$env:UV_PUBLISH_TOKEN = "pypi-xxxxxxxx"

# 方式二：用户名 + 密码
$env:UV_PUBLISH_USERNAME = "__token__"
$env:UV_PUBLISH_PASSWORD = "pypi-xxxxxxxx"
```

### 完整流程

```powershell
# 1. 创建库项目
uv init --lib my-lib

# 2. 写代码、加依赖
cd my-lib
# ... 编辑 src/my_lib/__init__.py ...
uv add requests

# 3. 升级版本号（每次发布必须不同版本）
uv version --bump minor     # 0.1.0 → 0.2.0

# 4. 构建
uv build                    # 生成 dist/*.tar.gz 和 dist/*.whl

# 5. 发布到 PyPI
$env:UV_PUBLISH_TOKEN = "pypi-xxxxxxxx"
uv publish                  # 上传到 PyPI

# 6. 别人就能装了
# pip install my-lib
```

### 什么时候不需要构建和发布？

| 你的项目类型 | 需要 build？ | 需要 publish？ |
|------------|------------|--------------|
| 写个 FastAPI Web 服务自己部署 | ❌ 不需要 | ❌ 不需要 |
| 写个数据分析脚本自己用 | ❌ 不需要 | ❌ 不需要 |
| 写个库给同事用（同一个仓库） | ❌ 直接 `uv add --editable ../my-lib` | ❌ 不需要 |
| 写个库发布到全网 | ✅ 需要 build | ✅ 需要 publish |

---

## pip 兼容模式

uv 提供了 `pip` 子命令，完全兼容 pip 的接口，但速度更快。

```powershell
# 等价于 pip install
uv pip install requests

# 等价于 pip list
uv pip list

# 等价于 pip freeze
uv pip freeze

# 等价于 pip show
uv pip show fastapi
```

但**建议优先使用项目模式**（`uv add` / `uv sync`），而不是 `uv pip`。

---

## 配置 uv

### 为什么需要配置？

uv 的默认配置对大多数项目已经够用。配置是为了解决**特殊情况**：

| 场景                       | 问题                                  | 解决方法                   |
| ------------------------ | ----------------------------------- | ---------------------- |
| 你的 C 盘空间不够               | uv 默认把缓存下到 `C:\Users\xxx\.cache\uv` | 改缓存路径                  |
| 公司内部有自己的 PyPI 服务器        | 默认从 pypi.org 下载，公司内网访问不了            | 加私有索引源                 |
| 你在国内，pypi.org 太慢         | 装个包等半天                              | 换成国内镜像源                |
| 你希望每个项目自动用 uv 管理的 Python | 默认可能用系统安装的 Python                   | 设置 `python-preference` |
| CI 环境想加速                 | 每次重新下载所有包太慢                         | 配置缓存复用                 |


### 三种配置方式（优先级从高到低）

| 方式 | 写在哪儿 | 生效范围 | 会不会提交到 git |
|------|---------|---------|----------------|
| **环境变量** | shell 配置文件或 CI 变量 | 当前终端/进程 | 不提交（写在 CI 配置里） |
| **uv.toml** | 项目根目录 | 当前项目 | 看情况，索引源等团队统一的可以提交 |
| **`[tool.uv]`** | `pyproject.toml` 里 | 当前项目 | **会**提交到 git（建议只放团队统一的配置） |

### 方式一：环境变量（临时改、CI 里用）

```powershell
# 临时换 PyPI 镜像源（国内加速）
$env:UV_DEFAULT_INDEX = "https://mirrors.ustc.edu.cn/pypi/simple"
uv add requests                # 从镜像源下载

# 临时省磁盘空间
$env:UV_NO_CACHE = "true"
uv sync

# 离线模式（没网的时候）
$env:UV_OFFLINE = "true"
uv sync
```

常用环境变量说明：

| 变量 | 什么时候用 | 例子 |
|------|-----------|------|
| `UV_DEFAULT_INDEX` | 国内用镜像源加速，或公司有内部 PyPI | `https://mirrors.tuna.tsinghua.edu.cn/pypi/simple` |
| `UV_PUBLISH_TOKEN` | 发布到 PyPI 时 | `pypi-xxxxxxxx` |
| `UV_CACHE_DIR` | C 盘空间不够，挪到别的盘 | `D:\.uv-cache` |
| `UV_NO_CACHE` | 临时不想写缓存 | `true` |
| `UV_OFFLINE` | 没网的环境（如隔离机房） | `true` |
| `UV_COMPILE_BYTECODE` | 生产环境追求启动速度，安装时预编译 `.pyc` | `true` |
| `UV_LINK_MODE` | 不同项目之间想省磁盘空间（硬链接共享包） | `hardlink` |

### 方式二：`uv.toml`（项目专属、不污染 pyproject.toml）

`uv.toml` 放在项目根目录，跟 `pyproject.toml` 同级。适合放**不想提交到 git** 或个人偏好的配置：

```toml
# uv.toml — 这个文件不会影响 pyproject.toml 的整洁
cache-dir = "D:\\.uv-cache"          # 缓存挪到 D 盘
python-preference = "managed"        # 优先用 uv 自己下载的 Python
```

### 方式三：`[tool.uv]` 写在 pyproject.toml 里（团队共享）

适合放在 git 里、团队统一的配置：

```toml
# pyproject.toml

[tool.uv]
package = true          # 这个项目是可分发包（等价于 --package 模式）
dev-dependencies = []   # 旧方式写 dev 依赖，现在推荐用 [dependency-groups]
```

### 私有包索引（公司内部 PyPI）

很多公司不会把内部库发到公开的 pypi.org，而是自己搭一个 PyPI 服务器。你需要告诉 uv 去哪里找这些包：

**方式一：命令参数（一次性）**

```powershell
uv add --index name=internal,url=http://my-pypi.com/simple/ my-private-lib
```

**方式二：写在 pyproject.toml 里（长期有效）**

```toml
[[tool.uv.index]]
name = "internal"
url = "http://my-pypi.com/simple/"
```

之后所有依赖解析都会先查这个索引源。

### 需要我帮你配一个吗？

如果你是新手，大部分配置你根本用不到。唯一可能用到的是：

```powershell
# 国内用户选一个镜像源写到 $PROFILE 里
$env:UV_DEFAULT_INDEX = "https://mirrors.tuna.tsinghua.edu.cn/pypi/simple"
```

其他配置等你遇到具体问题（C 盘满了 / 公司有内部源 / 发布到 PyPI）再来翻这部分就行。

---

## 工作空间（Monorepo）

uv 支持一个仓库包含多个子包（workspace）：

```
my-monorepo/
  pyproject.toml              # workspace root
  packages/
    core/
      pyproject.toml
      src/
        core/
          ...
    cli/
      pyproject.toml
      src/
        cli/
          ...
```

在根 `pyproject.toml` 中声明：

```toml
[tool.uv.workspace]
members = ["packages/*"]
```

子包之间可以用 `uv add --workspace` 互相引用：

```powershell
uv add --workspace core
```

---

## uv 缓存管理

```powershell
# 查看缓存大小
uv cache dir

# 清理所有缓存
uv cache clean

# 清理指定包的缓存
uv cache clean requests
```

---

## 常用命令速查表

| 场景 | 命令 |
|------|------|
| 创建项目 | `uv init my-project` |
| 添加依赖 | `uv add fastapi` |
| 添加 dev 依赖 | `uv add --dev pytest` |
| 移除依赖 | `uv remove fastapi` |
| 同步环境 | `uv sync` |
| 锁定依赖 | `uv lock` |
| 运行脚本 | `uv run python main.py` |
| 运行测试 | `uv run pytest` |
| 安装 Python | `uv python install 3.12` |
| 锁定 Python | `uv python pin 3.12` |
| 安装全局工具 | `uv tool install ruff` |
| 临时运行工具 | `uvx black script.py` |
| 构建分发包 | `uv build` |
| 发布到 PyPI | `uv publish` |
| 导出 requirements | `uv export -o requirements.txt` |
| 查看依赖树 | `uv tree` |
| 升级所有包 | `uv sync --upgrade` |
| 升级单个包 | `uv sync --upgrade-package fastapi` |
| 清理缓存 | `uv cache clean` |

---

## 与 pip 工作流对比

| 传统 pip 方式 | uv 方式 |
|--------------|---------|
| `pip install requests` | `uv add requests` |
| `pip install -r requirements.txt` | `uv sync` |
| `pip freeze > requirements.txt` | `uv lock`（自动）+ `uv export` |
| `python -m venv .venv && .venv\Scripts\activate` | `uv sync` 自动创建并管理 `.venv` |
| `pip install pytest && pip freeze` | `uv add --dev pytest` |
| `pipx install ruff` | `uv tool install ruff` |
| `pyenv install 3.12` | `uv python install 3.12` |
| `pip install -e .` | `uv sync` 默认就是 editable |
| `python setup.py sdist bdist_wheel` | `uv build` |
| `twine upload dist/*` | `uv publish` |

---

## 与 poetry 对比

| 对比项 | uv | poetry |
|-------|-----|--------|
| 语言 | Rust | Python |
| 速度 | **极快** | 慢 |
| 依赖解析 | 极快 | 慢 |
| pyproject.toml 格式 | PEP 621 标准 | 自定义 `[tool.poetry]` |
| 依赖分组 | `[dependency-groups]`（PEP 735） | `[tool.poetry.group]` |
| 虚拟环境 | 自动管理 `.venv` | 自动管理 |
| Python 版本管理 | 内置 | 无，需配合 pyenv |
| 锁文件格式 | `uv.lock`（跨平台，含哈希） | `poetry.lock` |
| 构建后端 | 支持多种（uv/hatch/setuptools 等） | 仅自带的 build system |
| 插件系统 | 无 | 有 |
| 兼容 pip | 有 `uv pip` 子命令 | 不兼容 |
| 脚本支持 | PEP 723 内联元数据 | 无 |
| monorepo | 支持 workspace | 不原生支持 |

---

## 最佳实践

### 项目初始化

```powershell
uv init my-app --python 3.12
cd my-app
uv add fastapi uvicorn
uv add --dev pytest ruff mypy pytest-cov
```

### CI/CD 中

#### 先解释 CI/CD 是什么

你写完代码提交到 GitHub 之后，可能希望自动做几件事：

```text
你 git push 提交代码
    │
    ▼
CI（持续集成）                              ← 自动触发
    ├── 拉取你的最新代码
    ├── 装依赖（uv sync --frozen）
    ├── 跑测试（uv run pytest）
    ├── 检查代码格式（uv run ruff check）
    ├── 检查类型（uv run mypy）
    │
    ├── 全部通过 → 合并 PR
    │
    ▼
CD（持续部署/交付）                          ← 自动触发
    └── 把代码部署到服务器
```

**CI = 自动帮你检查代码有没有问题**（每次提交都跑一遍测试，不用等人工 review 时才发现坏了）

**CD = 自动帮你发布**（测试过了就自动部署到服务器或发布到 PyPI）

这些任务一般跑在 **GitHub Actions**、**GitLab CI**、**Jenkins** 之类的平台上，它们需要一个配置文件告诉它们怎么跑。

#### 实际例子：GitHub Actions 配置

这个 YAML 文件放在你仓库的 `.github/workflows/ci.yml`，GitHub 会自动识别并执行：

```yaml
# .github/workflows/ci.yml
name: CI

# 什么时候触发：每次推代码或提 PR 时
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4           # 1. 拉取代码

      - name: Install uv
        uses: astral-sh/setup-uv@v5         # 2. 安装 uv

      - name: Install dependencies
        run: uv sync --frozen               # 3. 按 uv.lock 装依赖（不修改 lock 文件）

      - name: Run tests
        run: uv run pytest                  # 4. 跑测试

      - name: Lint check
        run: uv run ruff check              # 5. 检查代码格式
```

每次你 `git push` 后，GitHub 就会自动拉你的代码，跑一遍这个流程。如果有测试失败了，你会在 PR 页面上看到一个红叉 ❌。

**对于你目前来说**：你只需要知道 CI/CD 是个「自动跑测试和部署的机器人」，用到的时候再来参考这个配置就行。

### 生产部署

```powershell
# 方法 1：直接使用 uv 环境
uv sync --no-dev
uv run uvicorn app:main

# 方法 2：导出 requirements.txt 给 Docker
uv export --no-dev -o requirements.txt
pip install -r requirements.txt
```

### 常用技巧

1. **不要手动激活 .venv** — 用 `uv run` 代替
2. **`uv sync --frozen`** 在 CI 中使用，确保 lock 文件不变
3. **`uv run --with`** 临时带上依赖而不污染项目
4. **`uvx`** 临时运行工具，用完即走
5. **`uv cache clean`** 定期清理
6. **`.python-version` 提交到 git**，保证团队统一 Python 版本

