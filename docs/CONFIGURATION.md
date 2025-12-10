# 配置管理指南

## 概述

系统使用 `config.py` 模块统一管理配置信息，特别是敏感的 API Key。这种方式提供了更好的安全性和灵活性。

## 配置方式

### 1. 使用 .env 文件（推荐）

这是最安全和便捷的方式，适合本地开发。

**步骤**:

1. 复制示例文件：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件：
```bash
# AWS Bedrock 配置
AWS_BEDROCK_API_KEY=your-actual-api-key-here
AWS_BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0
```

3. 在代码中使用：
```python
from config import setup_config

# 自动从 .env 文件加载
setup_config()
```

**优点**:
- ✅ API Key 不会被提交到 Git（`.env` 已在 `.gitignore` 中）
- ✅ 易于管理和修改
- ✅ 团队成员可以使用各自的配置

### 2. 使用环境变量

适合生产环境或 CI/CD 流程。

**临时设置**（当前会话）:
```bash
export AWS_BEDROCK_API_KEY='your-api-key'
export AWS_BEDROCK_MODEL_ID='us.anthropic.claude-sonnet-4-20250514-v1:0'
```

**永久设置**（添加到 shell 配置文件）:

对于 bash:
```bash
echo 'export AWS_BEDROCK_API_KEY="your-api-key"' >> ~/.bashrc
source ~/.bashrc
```

对于 zsh:
```bash
echo 'export AWS_BEDROCK_API_KEY="your-api-key"' >> ~/.zshrc
source ~/.zshrc
```

**在代码中使用**:
```python
from config import setup_config

# 自动从环境变量加载
setup_config()
```

### 3. 在代码中直接设置

适合测试或特殊场景。

```python
from config import setup_config

# 直接提供 API Key
setup_config(
    api_key='your-api-key',
    model_id='us.anthropic.claude-sonnet-4-20250514-v1:0'
)
```

**注意**: 不要在提交到 Git 的代码中硬编码 API Key！

## 配置优先级

当多种配置方式同时存在时，优先级从高到低：

1. **代码中直接设置** - `setup_config(api_key='...')`
2. **环境变量** - `export AWS_BEDROCK_API_KEY='...'`
3. **`.env` 文件** - `.env` 文件中的配置

## 配置验证

系统会自动验证配置是否完整：

```python
from config import ensure_configured

try:
    config = ensure_configured()
    print("✓ 配置验证通过")
except ValueError as e:
    print(f"✗ 配置验证失败: {e}")
```

如果 API Key 未配置，会抛出详细的错误信息，指导如何配置。

## 配置项说明

### AWS_BEDROCK_API_KEY（必需）

AWS Bedrock 的 API Key，用于认证。

**获取方式**: 从 AWS Bedrock 控制台获取

**格式**: `bedrock-api-key-...`

### AWS_BEDROCK_MODEL_ID（可选）

使用的模型 ID。

**默认值**: `us.anthropic.claude-sonnet-4-20250514-v1:0`

**其他可选值**:
- `us.anthropic.claude-sonnet-3-5-20241022-v2:0`
- `us.anthropic.claude-opus-4-20250514-v1:0`

## 安全最佳实践

### ✅ 推荐做法

1. **使用 .env 文件**存储本地开发的 API Key
2. **使用环境变量**在生产环境中配置
3. **定期轮换** API Key
4. **限制权限**，只授予必要的 AWS 权限
5. **不要分享** API Key

### ❌ 避免做法

1. ❌ 在代码中硬编码 API Key
2. ❌ 将 `.env` 文件提交到 Git
3. ❌ 在公开的地方（如 GitHub Issues）暴露 API Key
4. ❌ 使用生产环境的 API Key 进行测试
5. ❌ 与他人共享 API Key

## 故障排查

### 问题 1: "AWS Bedrock API Key 未配置"

**原因**: 系统找不到 API Key

**解决方案**:
1. 检查 `.env` 文件是否存在且包含 `AWS_BEDROCK_API_KEY`
2. 检查环境变量是否设置：`echo $AWS_BEDROCK_API_KEY`
3. 确保在代码中调用了 `setup_config()`

### 问题 2: ".env 文件不生效"

**原因**: `.env` 文件位置不正确或格式错误

**解决方案**:
1. 确保 `.env` 文件在项目根目录
2. 检查文件格式：`KEY=value`（不要有空格）
3. 不要使用引号包围值（除非值本身包含空格）

### 问题 3: "API Key 无效"

**原因**: API Key 过期或格式错误

**解决方案**:
1. 从 AWS Bedrock 控制台重新生成 API Key
2. 检查 API Key 是否完整复制（没有多余的空格或换行）
3. 确认 API Key 有正确的权限

## 示例代码

### 基础使用

```python
from config import setup_config
from hierarchy_system import HierarchyBuilder

# 设置配置
setup_config()

# 创建团队
agent, tracker, team_names = (
    HierarchyBuilder()
    .set_global_prompt("...")
    .add_team(...)
    .build()
)
```

### 高级使用

```python
from config import get_config, setup_config

# 方式 1: 自动加载
setup_config()

# 方式 2: 手动指定
setup_config(
    api_key='your-api-key',
    model_id='us.anthropic.claude-sonnet-4-20250514-v1:0'
)

# 获取配置实例
config = get_config()

# 检查配置状态
if config.is_configured():
    print(f"使用模型: {config.model_id}")
else:
    print("API Key 未配置")
```

### 测试环境配置

```python
import os
from config import setup_config

# 测试环境使用测试 API Key
if os.getenv('ENVIRONMENT') == 'test':
    setup_config(api_key='test-api-key')
else:
    setup_config()  # 生产环境从 .env 加载
```

## 相关文件

- `config.py` - 配置管理模块
- `.env.example` - 配置文件模板
- `.env` - 实际配置文件（不提交到 Git）
- `.gitignore` - 确保 `.env` 不被提交

## 更多信息

如有问题，请查看：
- [README.md](../README.md) - 项目概述
- [requirements.md](requirements.md) - 需求文档
- [CONTEXT_SHARING_GUIDE.md](CONTEXT_SHARING_GUIDE.md) - 上下文共享指南
