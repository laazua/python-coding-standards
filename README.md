# Python Coding Standards

强制执行 PEP8 编码规范与严格类型约束的 Claude Code Skill。安装后在编写 Python 代码时自动介入，确保代码符合团队标准。

---

## 目录

- [安装 Skill](#安装-skill)
  - [方式一：全局安装（推荐）](#方式一全局安装推荐)
  - [方式二：项目级安装](#方式二项目级安装)
  - [安装后验证](#安装后验证)
- [在项目中使用](#在项目中使用)
  - [前置准备：安装 Python 依赖](#前置准备安装-python-依赖)
  - [场景 1：编写新代码（Skill 自动介入）](#场景-1编写新代码skill-自动介入)
  - [场景 2：命令行手动检查](#场景-2命令行手动检查)
  - [场景 3：安装 Git Hooks 自动拦截](#场景-3安装-git-hooks-自动拦截)
  - [场景 4：CI/CD 流水线集成](#场景-4cicd-流水线集成)
- [Skill 触发的具体场景](#skill-触发的具体场景)
- [脚本参考](#脚本参考)
- [常见问题](#常见问题)

---

## 安装 Skill

### 方式一：全局安装（推荐）

全局安装后，**所有**你通过 Claude Code 编辑的 Python 项目都会自动应用此标准。

```bash
# 1. 进入 skill 目录
cd /opt/codes/python-coding-standards

# 2. 复制到 Claude Code 全局 skills 目录
mkdir -p ~/.claude/skills/python-coding-standards
cp -r SKILL.md scripts config hooks tests ~/.claude/skills/python-coding-standards/

# 3. 安装 Python 依赖（一次性）
pip install black>=23.0.0 mypy>=1.0.0 pylint>=3.0.0 isort>=5.12.0
```

完成。之后在**任意目录**打开 Claude Code 编辑 `.py` 文件，skill 会自动激活。

### 方式二：项目级安装

只在特定项目中启用此 skill：

```bash
# 1. 进入你的 Python 项目
cd /path/to/your-python-project

# 2. 创建项目 skills 目录并复制
mkdir -p .claude/skills/python-coding-standards
cp -r /opt/codes/python-coding-standards/SKILL.md \
      /opt/codes/python-coding-standards/scripts \
      /opt/codes/python-coding-standards/config \
      /opt/codes/python-coding-standards/hooks \
      /opt/codes/python-coding-standards/tests \
      .claude/skills/python-coding-standards/

# 3. 安装 Python 依赖
pip install black>=23.0.0 mypy>=1.0.0 pylint>=3.0.0 isort>=5.12.0
```

> **提示：** 项目级 skill 优先级高于全局 skill。如果不同项目需要不同的编码标准，使用此方式。

### 安装后验证

在 Claude Code 中输入以下任意一句话，如果 skill 正确安装，它会自动介入：

```
帮我写一个 Python 函数，用来解析 CSV 文件
```

Claude Code 生成的代码会自动遵循：
- 4 空格缩进、79 字符行宽
- `snake_case` 函数名
- 所有参数和返回值带类型注解
- 包含 docstring

---

## 在项目中使用

### 前置准备：安装 Python 依赖

Skill 内部调用 black、isort、mypy、pylint 进行检查。在使用前先安装：

```bash
pip install black>=23.0.0 mypy>=1.0.0 pylint>=3.0.0 isort>=5.12.0
```

> 这些依赖在 SKILL.md 的 `dependencies` 字段中声明。如果未安装，skill 中的格式化脚本会跳过对应步骤并给出提示。

---

### 场景 1：编写新代码（Skill 自动介入）

这是最常用的方式——让 Claude Code 帮你写代码，skill 自动保证合规。

**步骤：**

1. 在 Claude Code 中打开任意 Python 项目
2. 直接描述你的需求，Claude 按标准生成代码
3. 生成后，skill 自动运行检查器验证
4. 如有违规，skill 会指出并要求 Claude 修正

**示例对话：**

```
你: 帮我写一个缓存装饰器，支持 TTL 过期

Claude（自动激活 skill 后生成）:
```

```python
"""Cache decorator with TTL support."""

import functools
import time
from typing import Any, Callable, Optional, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def cached(ttl_seconds: float = 300.0) -> Callable[[F], F]:
    """Decorate a function with a time-to-live cache.

    Args:
        ttl_seconds: Cache expiration time in seconds.
                     Defaults to 300 (5 minutes).

    Returns:
        A decorated function with TTL-based caching.
    """
    cache: dict[str, tuple[float, Any]] = {}

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = f"{args}:{kwargs}"
            now = time.monotonic()

            if key in cache:
                expiry, value = cache[key]
                if now < expiry:
                    return value

            result = func(*args, **kwargs)
            cache[key] = (now + ttl_seconds, result)
            return result

        return wrapper  # type: ignore[return-value]

    return decorator
```

```bash
# Skill 自动在后台运行:
$ python3 scripts/pep8_checker.py cache_decorator.py
✓ cache_decorator.py: No PEP8 violations found.

$ python3 scripts/type_validator.py cache_decorator.py
✓ cache_decorator.py: All type hints present.
```

> **注意：** 实际运行检查脚本需要脚本文件在本地。参见下一节"命令行手动检查"。

---

### 场景 2：命令行手动检查

当你想自己验证代码合规性时，直接调用检查脚本。

**第一步：复制 scripts 到你项目的根目录**

> 如果你用的是全局安装，scripts 在 `~/.claude/skills/python-coding-standards/scripts/`。以下假设你已经复制到项目或调整了路径。

```bash
# 从 skill 目录复制 scripts 到当前项目
cp -r ~/.claude/skills/python-coding-standards/scripts ./
```

**第二步：运行检查**

```bash
# === PEP8 检查 ===
python3 scripts/pep8_checker.py my_module.py
# 输出示例:
#   line 8: [E101] Tab characters are not allowed; use 4 spaces.
#   line 42: [E501] Line too long (95/79 characters).

# === 类型注解检查 ===
python3 scripts/type_validator.py my_module.py
# 输出示例:
#   line 15 [ERROR] 'calculate': Parameter 'x' is missing a type annotation.

# === 自动格式化（原地修改文件） ===
python3 scripts/auto_formatter.py my_module.py
# 输出: ↻ my_module.py: Formatted

# === 格式化前先看看会改什么 ===
python3 scripts/auto_formatter.py my_module.py --diff

# === 只检查不修改（CI 模式） ===
python3 scripts/auto_formatter.py my_module.py --check

# === JSON 输出（方便接其他工具） ===
python3 scripts/pep8_checker.py my_module.py --json
python3 scripts/type_validator.py my_module.py --json
```

**第三步：批量检查整个项目**

```bash
# 检查所有 .py 文件（跳过虚拟环境）
find . -name "*.py" \
  -not -path "*/.venv/*" \
  -not -path "*/venv/*" \
  -not -path "*/__pycache__/*" \
  -not -path "*/migrations/*" | while read f; do
    python3 scripts/pep8_checker.py "$f" --quiet
    python3 scripts/type_validator.py "$f" --quiet
done
```

**退出码含义：**

| 退出码 | PEP8 | Type Validator |
|--------|------|----------------|
| 0 | 无违规 | 类型注解完整 |
| 1 | 有违规 | 有缺失 |
| 2 | 文件不存在 | 文件不存在 |
| 3 | 运行异常 | 运行异常 |

---

### 场景 3：安装 Git Hooks 自动拦截

在代码提交和推送环节自动检查，不合格的代码无法入库。

**安装 Hook：**

```bash
# 从 skill 目录复制 hooks（全局安装路径）
cp ~/.claude/skills/python-coding-standards/hooks/pre-commit .git/hooks/
chmod +x .git/hooks/pre-commit

cp ~/.claude/skills/python-coding-standards/hooks/pre-push .git/hooks/
chmod +x .git/hooks/pre-push

# 确认已安装
ls -la .git/hooks/pre-commit .git/hooks/pre-push
```

**Hook 执行流程：**

```
git commit -m "add feature"
    │
    ├─ 1. 自动格式化 staged 的 .py 文件 (black + isort)
    ├─ 2. PEP8 合规检查
    ├─ 3. 有违规 → 拒绝提交，打印修复建议
    └─ 4. 通过     → 允许提交

git push origin main
    │
    ├─ 1. 类型注解验证（所有 .py 文件）
    ├─ 2. 运行单元测试（如果项目有 tests/ 目录）
    ├─ 3. 有失败 → 拒绝推送
    └─ 4. 通过     → 允许推送
```

**手动测试 Hook：**

```bash
# 测试 pre-commit（不实际提交）
echo 'x=1  ' > test_hook.py && git add test_hook.py
bash .git/hooks/pre-commit
# 预期输出: ✗ test_hook.py — formatting issues found
#           → Auto-formatted and re-staged

# 测试 pre-push（不实际推送）
bash .git/hooks/pre-push

# 清理测试文件
rm -f test_hook.py
```

---

### 场景 4：CI/CD 流水线集成

在 GitHub Actions 或 GitLab CI 中自动运行全套检查。

**GitHub Actions：**

```yaml
# .github/workflows/python-standards.yml
name: Python Standards Check

on: [push, pull_request]

jobs:
  standards:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install black isort mypy pylint
          pip install -r requirements.txt 2>/dev/null || true

      - name: Copy check scripts
        run: |
          cp -r ~/.claude/skills/python-coding-standards/scripts ./

      - name: Check formatting
        run: python3 scripts/auto_formatter.py . --check

      - name: PEP8 compliance
        run: |
          find . -name "*.py" -not -path "*/.venv/*" \
            -exec python3 scripts/pep8_checker.py {} --quiet \;

      - name: Type validation
        run: |
          find . -name "*.py" -not -path "*/.venv/*" \
            -exec python3 scripts/type_validator.py {} --quiet \;

      - name: Run tests
        run: python3 -m pytest tests/ -v
```

**GitLab CI：**

```yaml
# .gitlab-ci.yml
python-standards:
  image: python:3.12
  before_script:
    - pip install black isort mypy pylint
    - cp -r ~/.claude/skills/python-coding-standards/scripts ./
  script:
    - python3 scripts/auto_formatter.py . --check
    - find . -name "*.py" -not -path "*/.venv/*" -exec python3 scripts/pep8_checker.py {} --quiet \;
    - find . -name "*.py" -not -path "*/.venv/*" -exec python3 scripts/type_validator.py {} --quiet \;
    - python3 -m pytest tests/ -v
```

---

## Skill 触发的具体场景

Skill 在以下情况**自动激活**，无需手动调用：

| 触发条件 | 行为 |
|----------|------|
| 你创建/编辑 `.py` 文件 | 写入代码后自动按 PEP8 + 类型规范生成 |
| 你问 "这段 Python 代码有什么问题" | 按编码标准逐条审查 |
| 你请求 "review 这个 Python PR" | 检查 PEP8、类型注解、命名规范 |
| 你问 "Python 类型注解怎么写" | 给出符合本项目标准的写法 |
| 你提到 "coding standards" 或 "PEP8" | 激活当前标准上下文 |
| 你写了一个函数但没有类型注解 | Skill 会提醒补充类型注解 |

**示例对话效果对比：**

```
没有 Skill 时:
  你: 写一个处理用户数据的函数
  Claude: def process(data):              ← 无类型、无docstring
              return data["name"].upper()

有 Skill 时:
  你: 写一个处理用户数据的函数
  Claude: def process_user_name(data: dict[str, str]) -> str:   ← 完整类型
              """Extract and uppercase the user name.
              
              Args:
                  data: A mapping of user fields.
                  
              Returns:
                  The uppercased user name.
              """
              return data["name"].upper()
```

---

## 脚本参考

### pep8_checker.py

```bash
python3 scripts/pep8_checker.py <file> [--json] [--quiet]
```

检查的规则：

| 规则码 | 内容 | 严重度 |
|--------|------|--------|
| E101 | Tab 缩进 | Error |
| E201 | 括号内前导空格 | Error |
| E202 | 括号内尾部空格 | Error |
| E302 | 顶层定义前缺少 2 空行 | Error |
| E303 | 类方法间缺少空行 | Error |
| E401 | 一行多个 import | Error |
| E402 | import 顺序错误 | Error |
| E501 | 行宽超限 (代码 79/文档 72) | Error |
| W291 | 行尾空格 | Warning |
| W292 | 文件末尾无换行 | Warning |
| N801 | 类名非 PascalCase | Error |
| N802 | 函数名非 snake_case | Error |
| E999 | 通配符导入 | Error |

### type_validator.py

```bash
python3 scripts/type_validator.py <file> [--json] [--mypy]
```

检查项：

- [ERROR] 参数缺少类型注解
- [ERROR] 返回值缺少类型注解
- [ERROR] `*args` / `**kwargs` 缺少类型注解
- [WARNING] 使用 `Any` 而非具体类型
- [WARNING] 公开函数缺少 docstring

自动豁免：`self`/`cls`、`__init__`/`__str__` 等 dunder 方法、`@property`

### auto_formatter.py

```bash
python3 scripts/auto_formatter.py <file|directory> [--check] [--diff]
```

内部调用 black（代码格式化）+ isort（import 排序），配置来自 `config/pyproject.toml`。

---

## 常见问题

### Q: 我在项目中的 scripts/ 从哪里来？

全局安装 skill 后，scripts 在 `~/.claude/skills/python-coding-standards/scripts/`。使用以下命令复制到当前项目：

```bash
cp -r ~/.claude/skills/python-coding-standards/scripts ./
```

### Q: 如何只检查修改过的文件（更快）？

```bash
git diff --name-only HEAD | grep '\.py$' | while read f; do
    python3 scripts/pep8_checker.py "$f" --quiet
    python3 scripts/type_validator.py "$f" --quiet
done
```

### Q: pip 安装的包名是什么？

没有 pip 包。这是一个 Claude Code Skill + 配套命令行脚本。安装方式是将 SKILL.md 放入 `~/.claude/skills/` 或项目的 `.claude/skills/` 目录。

### Q: 可以自定义行宽吗？

可以。编辑 `config/pyproject.toml` 中 `line-length` 的值，以及 `config/.pylintrc` 中 `max-line-length`，保持两者一致。

### Q: black/isort 未安装怎么办？

格式化脚本会跳过对应步骤（不影响 PEP8 检查和类型验证）。安装：

```bash
pip install black isort
```

### Q: 如何在团队中统一使用？

1. 将本 skill 目录提交到团队仓库
2. 每个成员执行项目级安装（方式二）
3. 在 `.pre-commit-config.yaml` 中配置 hooks
4. CI/CD 流水线中集成检查脚本

---

## 项目结构

```
python-coding-standards/
├── SKILL.md                           # Skill 入口（Claude Code 识别此文件）
├── README.md                          # 本文件
├── .gitignore
├── scripts/
│   ├── pep8_checker.py               # PEP8 合规检查器
│   ├── type_validator.py             # 类型注解验证器
│   └── auto_formatter.py             # 自动格式化（black + isort）
├── config/
│   ├── pyproject.toml                 # black / isort / pytest 配置
│   ├── .pylintrc                      # pylint 规则
│   ├── .pre-commit-config.yaml        # pre-commit 框架配置
│   └── mypy.ini                       # mypy 严格模式配置
├── hooks/
│   ├── pre-commit                     # 提交前自动格式化 + PEP8 检查
│   └── pre-push                       # 推送前类型验证 + 测试
└── tests/
    ├── test_pep8_compliance.py        # 21 个 PEP8 测试用例
    └── test_type_hints.py            # 18 个类型验证测试用例
```
