# 动态层级团队系统文档

## 概述

动态层级团队系统是一个**配置驱动**的多智能体框架，允许你通过配置文件动态构建层级团队，而无需为每个 Agent 编写硬编码。

### 核心优势

✅ **通用组件** - 使用通用的 Global Supervisor、Team Supervisor 和 Worker Agent  
✅ **配置驱动** - 通过配置文件定义团队结构和行为  
✅ **动态构建** - 运行时动态创建 Agent，无需重启  
✅ **灵活扩展** - 轻松添加新团队、成员或修改配置  
✅ **多种配置方式** - 支持字典、构建器 API、预定义模板  

## 系统架构

### 核心组件

```
┌─────────────────────────────────────────┐
│   GlobalSupervisorFactory               │
│   (全局协调者工厂)                       │
│   - 根据配置创建 Global Supervisor       │
└──────────────┬──────────────────────────┘
               │
       ┌───────▼──────────┐
       │ TeamSupervisorFactory │
       │ (团队主管工厂)         │
       │ - 根据配置创建 Team Supervisor │
       └───────┬──────────┘
               │
       ┌───────▼──────────┐
       │ WorkerAgentFactory │
       │ (Worker 工厂)      │
       │ - 根据配置创建 Worker Agent │
       └──────────────────┘
```

### 配置数据结构

```python
GlobalConfig
├── system_prompt: str          # 全局协调者提示词
├── model: Optional[Any]        # 模型配置
└── teams: List[TeamConfig]     # 团队列表
    │
    └── TeamConfig
        ├── name: str                    # 团队名称
        ├── supervisor_prompt: str       # 主管提示词
        ├── model: Optional[Any]         # 模型配置
        └── workers: List[WorkerConfig]  # 成员列表
            │
            └── WorkerConfig
                ├── name: str            # 成员名称
                ├── role: str            # 角色描述
                ├── system_prompt: str   # 系统提示词
                ├── tools: List[Any]     # 工具列表
                ├── model: Optional[Any] # 模型配置
                ├── temperature: float   # 温度参数
                └── max_tokens: int      # 最大 token
```

## 使用方法

### 方式 1: 使用预定义配置

最简单的方式，使用默认配置快速开始：

```python
from dynamic_hierarchy_system import create_default_hierarchy

# 创建默认的层级团队
global_agent = create_default_hierarchy()

# 使用
response = global_agent("开发一个用户登录功能")
print(response)
```

默认配置包含：
- **技术团队**: 开发工程师、测试工程师
- **业务团队**: 市场专员、数据分析师

### 方式 2: 使用构建器 API

使用流式 API 构建自定义配置：

```python
from dynamic_hierarchy_system import HierarchyBuilder
from strands_tools import calculator, python_repl, editor

# 使用构建器创建自定义团队
global_agent = (
    HierarchyBuilder()
    .set_global_prompt("你是公司的全局协调者...")
    .add_team(
        name="研发团队",
        supervisor_prompt="你是研发团队主管...",
        workers=[
            {
                'name': '后端工程师',
                'role': '负责后端开发',
                'system_prompt': '你是后端工程师...',
                'tools': [python_repl, editor]
            },
            {
                'name': '前端工程师',
                'role': '负责前端开发',
                'system_prompt': '你是前端工程师...',
                'tools': [editor]
            }
        ]
    )
    .add_team(
        name="市场团队",
        supervisor_prompt="你是市场团队主管...",
        workers=[
            {
                'name': '市场专员',
                'role': '负责市场推广',
                'system_prompt': '你是市场专员...',
                'tools': [calculator]
            }
        ]
    )
    .build()
)

# 使用
response = global_agent("你的任务")
```

### 方式 3: 使用字典配置

使用字典定义完整配置，适合从配置文件加载：

```python
from dynamic_hierarchy_system import create_custom_hierarchy
from strands_tools import calculator, python_repl

config = {
    'global_prompt': '你是全局协调者...',
    'teams': [
        {
            'name': '技术团队',
            'supervisor_prompt': '你是技术团队主管...',
            'workers': [
                {
                    'name': '开发工程师',
                    'role': '负责开发',
                    'system_prompt': '你是开发工程师...',
                    'tools': [python_repl]
                }
            ]
        }
    ]
}

global_agent = create_custom_hierarchy(config)
```

### 方式 4: 使用预定义模板

使用 `config_examples.py` 中的预定义配置：

```python
from config_examples import SOFTWARE_DEV_CONFIG, ECOMMERCE_CONFIG
from dynamic_hierarchy_system import create_custom_hierarchy

# 使用软件开发团队配置
dev_agent = create_custom_hierarchy(SOFTWARE_DEV_CONFIG)

# 使用电商运营团队配置
ecommerce_agent = create_custom_hierarchy(ECOMMERCE_CONFIG)
```

## 配置示例

### 示例 1: 简单的两人团队

```python
config = {
    'global_prompt': '你是项目协调者。',
    'teams': [
        {
            'name': '开发团队',
            'supervisor_prompt': '你是开发团队主管。',
            'workers': [
                {
                    'name': '开发者',
                    'role': '编写代码',
                    'system_prompt': '你是开发者，擅长编程。',
                    'tools': [python_repl]
                },
                {
                    'name': '测试者',
                    'role': '测试代码',
                    'system_prompt': '你是测试者，擅长测试。',
                    'tools': [python_repl]
                }
            ]
        }
    ]
}
```

### 示例 2: 多团队协作

```python
config = {
    'global_prompt': '你是公司的全局协调者，管理技术和市场两个团队。',
    'teams': [
        {
            'name': '技术团队',
            'supervisor_prompt': '你是技术团队主管，协调开发工作。',
            'workers': [
                {
                    'name': '架构师',
                    'role': '系统架构设计',
                    'system_prompt': '你是架构师，擅长系统设计。',
                    'tools': [editor]
                },
                {
                    'name': '开发工程师',
                    'role': '代码实现',
                    'system_prompt': '你是开发工程师，擅长编码。',
                    'tools': [python_repl, editor]
                }
            ]
        },
        {
            'name': '市场团队',
            'supervisor_prompt': '你是市场团队主管，协调营销工作。',
            'workers': [
                {
                    'name': '营销专员',
                    'role': '市场推广',
                    'system_prompt': '你是营销专员，擅长推广。',
                    'tools': [http_request]
                },
                {
                    'name': '数据分析师',
                    'role': '数据分析',
                    'system_prompt': '你是数据分析师，擅长分析。',
                    'tools': [calculator, python_repl]
                }
            ]
        }
    ]
}
```

### 示例 3: 指定不同的模型

```python
from strands.models.anthropic import AnthropicModel

# 为不同的 Agent 指定不同的模型
config = {
    'global_prompt': '你是全局协调者。',
    'model': AnthropicModel(model_id="claude-sonnet-4-20250514"),  # 全局使用 Claude
    'teams': [
        {
            'name': '技术团队',
            'supervisor_prompt': '你是技术团队主管。',
            'model': None,  # 继承全局模型
            'workers': [
                {
                    'name': '开发工程师',
                    'role': '开发',
                    'system_prompt': '你是开发工程师。',
                    'tools': [python_repl],
                    'model': None  # 继承团队模型
                }
            ]
        }
    ]
}
```

## 完整示例场景

### 场景 1: 软件开发项目

```python
from config_examples import SOFTWARE_DEV_CONFIG
from dynamic_hierarchy_system import create_custom_hierarchy

# 创建软件开发团队
dev_team = create_custom_hierarchy(SOFTWARE_DEV_CONFIG)

# 任务 1: 开发新功能
task1 = """
开发一个用户认证系统:
1. 设计数据库表结构
2. 实现注册和登录 API
3. 创建前端登录页面
4. 编写单元测试和集成测试
5. 配置 CI/CD 流程
"""
response1 = dev_team(task1)

# 任务 2: 修复 Bug
task2 = """
生产环境出现性能问题:
1. 分析日志找出瓶颈
2. 优化数据库查询
3. 测试性能改进
4. 部署到生产环境
"""
response2 = dev_team(task2)
```

### 场景 2: 电商运营

```python
from config_examples import ECOMMERCE_CONFIG
from dynamic_hierarchy_system import create_custom_hierarchy

# 创建电商运营团队
ecommerce_team = create_custom_hierarchy(ECOMMERCE_CONFIG)

# 任务: 双十一大促
task = """
策划双十一大促活动:
1. 选品: 选择热门商品，制定价格策略
2. 营销: 设计促销活动，投放广告
3. 客服: 准备常见问题解答，培训客服团队
"""
response = ecommerce_team(task)
```

### 场景 3: 内容创作

```python
from config_examples import CONTENT_CREATION_CONFIG
from dynamic_hierarchy_system import create_custom_hierarchy

# 创建内容创作团队
content_team = create_custom_hierarchy(CONTENT_CREATION_CONFIG)

# 任务: 创作一篇文章
task = """
创作一篇关于 AI 技术的文章:
1. 撰写初稿
2. 审核内容质量和合规性
3. 优化标题和结构
4. 制定推广计划
5. 分析预期效果
"""
response = content_team(task)
```

## 高级特性

### 1. 动态添加团队成员

```python
from dynamic_hierarchy_system import HierarchyBuilder

builder = HierarchyBuilder()
builder.set_global_prompt("你是协调者...")

# 动态添加团队
for team_name in ['团队A', '团队B', '团队C']:
    builder.add_team(
        name=team_name,
        supervisor_prompt=f"你是{team_name}主管...",
        workers=[
            {
                'name': f'{team_name}成员1',
                'role': '角色1',
                'system_prompt': '提示词...',
                'tools': []
            }
        ]
    )

agent = builder.build()
```

### 2. 从 JSON 文件加载配置

```python
import json
from dynamic_hierarchy_system import create_custom_hierarchy

# 从 JSON 文件加载配置
with open('team_config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# 注意: 需要手动添加工具对象（JSON 无法序列化函数）
# 可以使用工具名称映射
tool_map = {
    'calculator': calculator,
    'python_repl': python_repl,
    'http_request': http_request
}

# 转换工具名称为工具对象
for team in config['teams']:
    for worker in team['workers']:
        worker['tools'] = [tool_map[t] for t in worker.get('tool_names', [])]

agent = create_custom_hierarchy(config)
```

### 3. 条件化团队配置

```python
def create_team_by_project_type(project_type: str):
    """根据项目类型创建不同的团队配置"""
    
    if project_type == 'web':
        return SOFTWARE_DEV_CONFIG
    elif project_type == 'ecommerce':
        return ECOMMERCE_CONFIG
    elif project_type == 'content':
        return CONTENT_CREATION_CONFIG
    else:
        return create_default_hierarchy()

# 使用
project_type = 'web'
agent = create_custom_hierarchy(create_team_by_project_type(project_type))
```

### 4. 团队配置继承

```python
# 基础配置
base_worker = {
    'temperature': 0.7,
    'max_tokens': 2048,
    'tools': [python_repl]
}

# 继承基础配置
developer = {
    **base_worker,
    'name': '开发工程师',
    'role': '开发',
    'system_prompt': '你是开发工程师...',
    'tools': [python_repl, editor]  # 覆盖工具
}
```

## 最佳实践

### 1. 系统提示词设计

**Global Supervisor 提示词**:
- 明确说明管理哪些团队
- 提供清晰的任务分配规则
- 说明如何协调跨团队协作

**Team Supervisor 提示词**:
- 列出团队成员及其专长
- 说明如何分配任务给成员
- 定义团队的职责范围

**Worker 提示词**:
- 明确角色和专长
- 提供具体的工作指导
- 说明输出格式要求

### 2. 工具配置

- 根据角色需求配置工具
- 避免给 Worker 配置过多工具
- 确保工具与职责匹配

### 3. 团队结构设计

- 保持 3 层结构（Global → Team → Worker）
- 每个团队 2-5 名成员为宜
- 避免团队职责重叠

### 4. 性能优化

- 使用 `callback_handler=None` 减少输出
- 合理设置 `max_tokens` 避免超限
- 考虑使用更快的模型（如 Claude Haiku）

### 5. 错误处理

```python
try:
    response = global_agent(task)
except Exception as e:
    print(f"任务执行失败: {e}")
    # 记录日志、重试或降级处理
```

## 与硬编码版本对比

| 特性 | 硬编码版本 | 动态配置版本 |
|------|-----------|-------------|
| 灵活性 | ❌ 需要修改代码 | ✅ 修改配置即可 |
| 可维护性 | ❌ 代码量大 | ✅ 配置清晰 |
| 扩展性 | ❌ 需要重新编译 | ✅ 运行时扩展 |
| 学习曲线 | ❌ 需要理解代码 | ✅ 只需理解配置 |
| 复用性 | ❌ 难以复用 | ✅ 配置可复用 |
| 调试难度 | ❌ 较难定位问题 | ✅ 配置清晰易调试 |

## 故障排除

### 问题 1: Worker 没有被调用

**原因**: Supervisor 的提示词不够清晰

**解决**: 在 Supervisor 提示词中明确说明何时使用哪个 Worker

### 问题 2: 任务路由错误

**原因**: Global Supervisor 提示词不够明确

**解决**: 提供更详细的任务分配规则和示例

### 问题 3: 输出混乱

**原因**: 没有设置 `callback_handler=None`

**解决**: 在 Supervisor 配置中添加 `callback_handler=None`

### 问题 4: 工具调用失败

**原因**: 工具配置错误或工具不可用

**解决**: 检查工具导入和配置

## 文件说明

- **dynamic_hierarchy_system.py** - 核心系统实现
- **config_examples.py** - 预定义配置示例
- **DYNAMIC_SYSTEM_README.md** - 本文档

## 下一步

1. 运行 `python dynamic_hierarchy_system.py` 查看演示
2. 运行 `python config_examples.py` 查看配置示例
3. 根据需求创建自己的配置
4. 参考 `config_examples.py` 中的模板

## 参考资源

- [Strands Agents 文档](https://docs.strands.ai/)
- [Multi-Agent Patterns](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/multi-agent/multi-agent-patterns/)
- [Agents as Tools](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/multi-agent/agents-as-tools/)

---

**开始构建你的动态层级团队吧！🚀**
