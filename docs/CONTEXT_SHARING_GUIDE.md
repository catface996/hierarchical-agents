# 跨 Team 上下文共享指南

## 概述

跨 Team 上下文共享功能允许后执行的团队自动接收先执行团队的研究成果，实现团队间的信息流动和协作。

**默认行为**：team 之间不共享上下文，每个团队独立工作。需要共享时才显式启用。

## 配置方式

### 1. 启用全局上下文共享

**默认情况**：
```python
# 默认不共享上下文
HierarchyBuilder()  # enable_context_sharing=False（默认）
```

**启用共享**：
```python
from hierarchy_system import HierarchyBuilder

agent, tracker, team_names = (
    HierarchyBuilder(enable_context_sharing=True)  # 显式启用全局开关
    .set_global_prompt("...")
    # ... 添加团队
    .build()
)
```

### 2. 配置团队级上下文接收

**默认情况**：
```python
.add_team(
    name="理论物理学团队",
    supervisor_prompt="...",
    workers=[...],
    # share_context=False（默认，不接收其他团队的上下文）
)
```

**启用接收**：
```python
.add_team(
    name="理论物理学团队",
    supervisor_prompt="...",
    workers=[...],
    share_context=False  # 显式设置：不接收其他团队的上下文
)
.add_team(
    name="实验物理学团队",
    supervisor_prompt="...",
    workers=[...],
    share_context=True  # 显式设置：接收已执行团队的上下文
)
```

**注意**：只有当全局开关 `enable_context_sharing=True` 时，`share_context=True` 才会生效。

## 工作机制

### 执行顺序

1. **Global Supervisor** 决定调用团队的顺序
2. **先执行的团队** 完成工作，结果被记录
3. **后执行的团队** 如果 `share_context=True`，会自动接收之前团队的结果

### 上下文传递格式

当团队接收到其他团队的上下文时，格式如下：

```
【原始任务】
你的任务描述...

【理论物理学团队的研究成果】：
[理论物理学团队] 理论分析结果...

【实验物理学团队的研究成果】：
[实验物理学团队] 实验设计方案...

【提示】：以上是其他团队已完成的工作，你可以参考这些成果来完成你的任务。

【成员执行状态】
  ✅ 量子理论专家 - 已执行
  ⭕ 实验设计师 - 未执行

【重要规则】：
- 只能调用"未执行"（⭕）的团队成员
- 已执行（✅）的成员不能再次调用
```

## 使用场景

### 场景 1：理论 → 实验

```python
.add_team(
    name="理论团队",
    supervisor_prompt="负责理论分析",
    workers=[...],
    share_context=False  # 理论团队独立工作
)
.add_team(
    name="实验团队",
    supervisor_prompt="基于理论设计实验",
    workers=[...],
    share_context=True  # 接收理论团队的成果
)
```

**效果**：实验团队可以看到理论团队的分析结果，基于理论来设计实验。

### 场景 2：多团队 → 评审

```python
.add_team(name="理论团队", ..., share_context=False)
.add_team(name="实验团队", ..., share_context=False)
.add_team(name="数据团队", ..., share_context=False)
.add_team(
    name="评审团队",
    supervisor_prompt="评估所有研究成果",
    workers=[...],
    share_context=True  # 接收所有团队的成果
)
```

**效果**：评审团队可以看到理论、实验、数据三个团队的所有成果，进行综合评审。

### 场景 3：流水线式协作

```python
.add_team(name="数据采集团队", ..., share_context=False)
.add_team(name="数据清洗团队", ..., share_context=True)  # 接收采集结果
.add_team(name="数据分析团队", ..., share_context=True)  # 接收清洗结果
.add_team(name="报告生成团队", ..., share_context=True)  # 接收分析结果
```

**效果**：形成数据处理流水线，每个团队基于前面团队的成果继续工作。

## 配置建议

### 1. 独立工作的团队

```python
share_context=False
```

适用于：
- 需要独立思考的团队
- 不依赖其他团队成果的团队
- 并发执行的团队

### 2. 依赖其他团队的团队

```python
share_context=True
```

适用于：
- 需要基于前期成果工作的团队
- 评审、总结类团队
- 后续处理团队

### 3. 在 System Prompt 中说明

建议在团队的 `supervisor_prompt` 中明确说明：

```python
supervisor_prompt="""你是实验物理学团队的负责人。

【重要】：你会收到理论团队的研究成果，请基于这些理论来设计实验。

你的职责：
1. 分析理论团队的成果
2. 设计验证实验
3. 评估实验可行性
"""
```

## 注意事项

1. **执行顺序很重要**：只有已执行的团队结果才会被传递
2. **避免循环依赖**：不要让团队相互依赖
3. **上下文大小**：如果团队很多，上下文可能会很大，注意 token 限制
4. **并发执行**：如果多个团队并发执行，它们看不到彼此的结果

## 完整示例

参见 `test_context_sharing.py` 文件，展示了完整的配置和使用方式。

## 与防重复机制的关系

- **防重复机制**：防止同一个 Team/Worker 被重复调用
- **上下文共享**：让不同 Team 之间可以共享信息
- **两者互补**：防重复避免浪费，上下文共享促进协作

## 性能考虑

- 上下文共享会增加传递给 Team 的信息量
- 如果团队很多，建议只让必要的团队开启 `share_context=True`
- 可以在 `supervisor_prompt` 中指导团队如何使用其他团队的成果
