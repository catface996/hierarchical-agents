# 团队执行模式说明

## 概述

系统支持两种团队执行模式：
- **顺序执行**（默认）：团队按顺序依次执行，适合有依赖关系的任务
- **并行执行**：团队可以同时执行，适合独立任务，提高效率

## 配置方式

### 方式 1：在构造函数中设置

```python
from hierarchy_system import HierarchyBuilder

# 顺序执行（默认）
builder = HierarchyBuilder(parallel_execution=False)

# 并行执行
builder = HierarchyBuilder(parallel_execution=True)
```

### 方式 2：使用链式方法设置

```python
from hierarchy_system import HierarchyBuilder

agent, tracker, teams = (
    HierarchyBuilder()
    .set_global_prompt("...")
    .set_parallel_execution(True)  # 设置为并行执行
    .add_team(...)
    .build()
)
```

## 使用场景

### 顺序执行（Sequential Execution）

**适用场景**：
- 任务之间有依赖关系
- 后续任务需要前面任务的结果
- 需要严格控制执行顺序

**示例**：
```python
agent, tracker, teams = (
    HierarchyBuilder(parallel_execution=False)  # 顺序执行
    .set_global_prompt("""你是项目协调者。
你需要按顺序完成以下任务：
1. 数据收集团队 - 收集数据
2. 数据分析团队 - 分析数据（依赖步骤1）
3. 报告撰写团队 - 撰写报告（依赖步骤2）
""")
    .add_team("数据收集团队", ..., workers=[...])
    .add_team("数据分析团队", ..., workers=[...])
    .add_team("报告撰写团队", ..., workers=[...])
    .build()
)
```

**执行流程**：
```
数据收集团队 → 完成 → 数据分析团队 → 完成 → 报告撰写团队
```

### 并行执行（Parallel Execution）

**适用场景**：
- 任务之间相互独立
- 不需要等待其他任务完成
- 希望提高执行效率

**示例**：
```python
agent, tracker, teams = (
    HierarchyBuilder(parallel_execution=True)  # 并行执行
    .set_global_prompt("""你是项目协调者。
以下团队可以同时工作：
1. 前端开发团队 - 开发用户界面
2. 后端开发团队 - 开发服务器逻辑
3. 测试团队 - 准备测试环境
""")
    .add_team("前端开发团队", ..., workers=[...])
    .add_team("后端开发团队", ..., workers=[...])
    .add_team("测试团队", ..., workers=[...])
    .build()
)
```

**执行流程**：
```
前端开发团队 ┐
后端开发团队 ├─ 同时执行
测试团队     ┘
```

## 工作原理

### 系统提示词引导

系统会根据 `parallel_execution` 参数自动在 Global Supervisor 的系统提示词中添加执行模式说明：

**顺序执行模式**：
```
【团队执行模式】：顺序执行
- 必须一个团队完成后再调用下一个团队
- 不能同时调用多个团队
- 按照逻辑顺序依次调用团队
```

**并行执行模式**：
```
【团队执行模式】：并行执行
- 可以同时调用多个团队
- 各团队独立工作，互不干扰
- 适合任务之间没有依赖关系的场景
```

### Agent 行为

- **顺序执行**：Agent 会理解需要按顺序调用团队工具，等待一个完成后再调用下一个
- **并行执行**：Agent 可以同时调用多个团队工具，各团队并发执行

## 性能对比

### 顺序执行
- **优点**：
  - 逻辑清晰，易于理解
  - 适合有依赖关系的任务
  - 资源占用相对较少
- **缺点**：
  - 总执行时间 = 各团队执行时间之和
  - 效率相对较低

### 并行执行
- **优点**：
  - 执行效率高
  - 总执行时间 ≈ 最慢团队的执行时间
  - 充分利用系统资源
- **缺点**：
  - 资源占用较多
  - 不适合有依赖关系的任务
  - 需要更多的 API 调用配额

## 最佳实践

### 1. 根据任务特性选择模式

```python
# 数据处理流水线 - 使用顺序执行
pipeline = HierarchyBuilder(parallel_execution=False)

# 独立模块开发 - 使用并行执行
development = HierarchyBuilder(parallel_execution=True)
```

### 2. 在系统提示词中明确说明

```python
# 顺序执行时，明确说明依赖关系
.set_global_prompt("""
任务必须按以下顺序执行：
1. 步骤A（必须先完成）
2. 步骤B（依赖步骤A的结果）
3. 步骤C（依赖步骤B的结果）
""")

# 并行执行时，明确说明独立性
.set_global_prompt("""
以下任务相互独立，可以同时进行：
1. 任务A
2. 任务B
3. 任务C
""")
```

### 3. 监控执行状态

```python
# 使用 tracker 监控执行状态
agent, tracker, teams = builder.build()

# 执行任务
response = agent(task)

# 查看统计信息
stats = tracker.get_statistics()
print(f"总调用次数: {stats['total_calls']}")
print(f"各团队调用次数: {stats['team_calls']}")
```

## 注意事项

1. **默认模式是顺序执行**，这是更安全的选择
2. **并行执行需要更多 API 配额**，注意成本控制
3. **系统提示词很重要**，要明确告诉 Agent 如何执行
4. **防重复机制仍然生效**，无论哪种模式都不会重复调用同一个团队

## 示例代码

完整示例请参考：
- `test/test_execution_modes.py` - 执行模式测试
- `test/test_quantum_research.py` - 量子力学研究（顺序执行示例）

## 相关文档

- [README.md](../README.md) - 项目概述
- [CONFIGURATION.md](CONFIGURATION.md) - 配置指南
- [CONTEXT_SHARING_GUIDE.md](CONTEXT_SHARING_GUIDE.md) - 上下文共享指南
