#!/usr/bin/env python3
"""
测试量子力学研究的层级团队系统 - 流式输出版本
"""
import os
import sys

# 添加父目录到路径，以便导入 hierarchy_system
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入配置管理模块
from src.core.config import setup_config

# 设置配置（自动从环境变量或 .env 文件加载）
setup_config()

# 运行完整测试
if __name__ == "__main__":
    from test_quantum_research_full import main
    main()
