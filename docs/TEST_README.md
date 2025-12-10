# 测试文件说明

本目录包含动态层级多智能体系统的所有测试文件。

## 测试文件列表

### 1. test_quantum_research_full.py
**完整的量子力学研究演示**

展示完整的三团队协作系统：
- 理论物理学团队（量子理论专家 + 数学物理学家）
- 实验物理学团队（实验设计师 + 数据分析师）
- 专家评审团队（方法论专家 + 同行评审专家）

运行方式：
```bash
python test/test_quantum_research_full.py
```

### 2. test_quantum_research.py
**快速测试入口**

调用 `test_quantum_research_full.py` 的简化版本。

运行方式：
```bash
python test/test_quantum_research.py
```

### 3. test_context_sharing.py
**跨 Team 上下文共享测试**

演示如何启用和使用跨团队上下文共享功能：
- 启用全局上下文共享开关
- 配置团队级上下文接收
- 验证上下文传递机制

运行方式：
```bash
python test/test_context_sharing.py
```

### 4. test_no_context_sharing.py
**默认行为测试（不共享上下文）**

验证默认情况下团队之间不共享上下文：
- 使用默认配置
- 验证团队独立工作
- 确认没有上下文传递

运行方式：
```bash
python test/test_no_context_sharing.py
```

### 5. test_function_names.py
**团队函数名生成测试**

测试团队名称到函数名的转换逻辑：
- 测试中文、英文、混合名称
- 验证符合 AWS Bedrock 规范
- 验证唯一性

运行方式：
```bash
python test/test_function_names.py
```

## 运行所有测试

```bash
# 从项目根目录运行
python test/test_function_names.py
python test/test_no_context_sharing.py
python test/test_context_sharing.py
python test/test_quantum_research_full.py
```

## 注意事项

1. **AWS Bedrock API Key**：所有测试文件都包含 API Key 配置
2. **路径导入**：所有测试文件都添加了父目录到 Python 路径
3. **独立运行**：每个测试文件都可以独立运行
4. **超时设置**：完整测试可能需要较长时间，请耐心等待

## 测试环境要求

- Python 3.8+
- strands
- strands-tools
- AWS Bedrock API Key

## 测试覆盖

- ✅ 基本功能测试
- ✅ 上下文共享功能测试
- ✅ 防重复调用机制测试
- ✅ 函数名生成逻辑测试
- ✅ 完整工作流测试
