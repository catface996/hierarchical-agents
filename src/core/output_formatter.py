"""
输出格式化模块 - 统一管理所有输出格式

提供一致的输出格式和样式，便于维护和修改。
"""

from typing import List, Optional


class OutputFormatter:
    """输出格式化器 - 统一管理所有输出样式"""
    
    # 分隔符长度
    SEPARATOR_LENGTH = 70
    
    # 分隔符样式
    SEPARATOR_WORKER = "="
    SEPARATOR_TEAM = "#"
    SEPARATOR_GLOBAL = "*"
    SEPARATOR_SECTION = "-"
    
    # ========================================================================
    # 消息生成器
    # ========================================================================
    
    @staticmethod
    def format_executed_message(name: str) -> str:
        """生成"已执行过"的返回消息"""
        return f"[{name}] 已在之前执行过，结果已在上文中，请直接引用"
    
    @staticmethod
    def format_duplicate_task_message(name: str) -> str:
        """生成"重复任务"的返回消息"""
        return f"[{name}] 已处理过相同任务，结果已在上文中，请直接引用"
    
    @staticmethod
    def format_result_message(name: str, response: str) -> str:
        """生成结果消息"""
        return f"[{name}] {response}"
    
    @staticmethod
    def _print_separator(char: str, length: int = SEPARATOR_LENGTH):
        """打印分隔符"""
        print(char * length)
    
    @staticmethod
    def _truncate_text(text: str, max_length: int = 100) -> str:
        """截断文本"""
        if len(text) > max_length:
            return f"{text[:max_length]}..."
        return text
    
    # ========================================================================
    # Worker Agent 输出
    # ========================================================================
    
    @staticmethod
    def print_worker_start(name: str, task: str):
        """打印 Worker 开始工作"""
        print(f"\n{OutputFormatter.SEPARATOR_WORKER * OutputFormatter.SEPARATOR_LENGTH}")
        print(f"🔬 {name} 开始工作")
        print(OutputFormatter.SEPARATOR_WORKER * OutputFormatter.SEPARATOR_LENGTH)
        print(f"📋 任务: {OutputFormatter._truncate_text(task)}")
        print(f"{OutputFormatter.SEPARATOR_WORKER * OutputFormatter.SEPARATOR_LENGTH}\n")
    
    @staticmethod
    def print_worker_thinking(name: str):
        """打印 Worker 思考过程标题"""
        print(f"💭 {name} 的思考过程:\n")
        print(OutputFormatter.SEPARATOR_SECTION * OutputFormatter.SEPARATOR_LENGTH + "\n")
    
    @staticmethod
    def print_worker_complete(name: str):
        """打印 Worker 完成工作"""
        print("\n" + OutputFormatter.SEPARATOR_SECTION * OutputFormatter.SEPARATOR_LENGTH)
        print(f"\n✅ {name} 完成工作\n")
    
    @staticmethod
    def print_worker_warning(message: str):
        """打印 Worker 警告信息"""
        print(f"\n{OutputFormatter.SEPARATOR_WORKER * OutputFormatter.SEPARATOR_LENGTH}")
        print(message)
        print(f"{OutputFormatter.SEPARATOR_WORKER * OutputFormatter.SEPARATOR_LENGTH}\n")
    
    @staticmethod
    def print_worker_duplicate_task_warning(name: str):
        """打印 Worker 重复任务警告（简化版）"""
        print(f"\n⚠️ [{name}] 该专家已经处理过此任务，请直接使用之前的结果\n")
    
    @staticmethod
    def print_worker_error(message: str):
        """打印 Worker 错误信息"""
        print(f"\n❌ {message}\n")
    
    # ========================================================================
    # Team Supervisor 输出
    # ========================================================================
    
    @staticmethod
    def print_team_start(name: str, call_id: str, task: str, workers: List[str]):
        """打印 Team Supervisor 开始协调"""
        print(f"\n{OutputFormatter.SEPARATOR_TEAM * OutputFormatter.SEPARATOR_LENGTH}")
        print(f"👔 {name}主管 开始协调")
        print(OutputFormatter.SEPARATOR_TEAM * OutputFormatter.SEPARATOR_LENGTH)
        print(f"📌 调用ID: {call_id}")
        print(f"📋 任务: {OutputFormatter._truncate_text(task)}")
        print(f"👥 团队成员: {', '.join(workers)}")
        print(f"{OutputFormatter.SEPARATOR_TEAM * OutputFormatter.SEPARATOR_LENGTH}\n")
    
    @staticmethod
    def print_team_thinking(name: str):
        """打印 Team Supervisor 协调过程标题"""
        print(f"💭 {name}主管的协调过程:\n")
        print(OutputFormatter.SEPARATOR_SECTION * OutputFormatter.SEPARATOR_LENGTH + "\n")
    
    @staticmethod
    def print_team_complete(name: str):
        """打印 Team Supervisor 完成协调"""
        print("\n" + OutputFormatter.SEPARATOR_SECTION * OutputFormatter.SEPARATOR_LENGTH)
        print(f"\n✅ {name}主管 完成协调\n")
    
    @staticmethod
    def print_team_warning(message: str):
        """打印 Team Supervisor 警告信息"""
        print(f"\n{OutputFormatter.SEPARATOR_TEAM * OutputFormatter.SEPARATOR_LENGTH}")
        print(message)
        print(f"{OutputFormatter.SEPARATOR_TEAM * OutputFormatter.SEPARATOR_LENGTH}\n")
    
    @staticmethod
    def print_team_error(message: str):
        """打印 Team Supervisor 错误信息"""
        print(f"\n❌ {message}\n")
    
    @staticmethod
    def print_team_duplicate_warning(message: str):
        """打印 Team Supervisor 重复调用警告"""
        print(f"\n⚠️  {message}\n")
    
    # ========================================================================
    # Global Supervisor 输出
    # ========================================================================
    
    @staticmethod
    def print_global_start(task: str):
        """打印 Global Supervisor 开始分析"""
        print(f"\n{OutputFormatter.SEPARATOR_GLOBAL * OutputFormatter.SEPARATOR_LENGTH}")
        print("🎯 首席科学家 (Global Supervisor) 开始分析")
        print(OutputFormatter.SEPARATOR_GLOBAL * OutputFormatter.SEPARATOR_LENGTH)
        print(f"📋 研究任务:\n{task}")
        print(f"{OutputFormatter.SEPARATOR_GLOBAL * OutputFormatter.SEPARATOR_LENGTH}\n")
    
    @staticmethod
    def print_global_thinking():
        """打印 Global Supervisor 分析过程标题"""
        print("💭 首席科学家的分析过程:\n")
        print(OutputFormatter.SEPARATOR_WORKER * OutputFormatter.SEPARATOR_LENGTH + "\n")
    
    @staticmethod
    def print_global_complete():
        """打印 Global Supervisor 完成分析"""
        print("\n" + OutputFormatter.SEPARATOR_WORKER * OutputFormatter.SEPARATOR_LENGTH)
        print("\n✅ 首席科学家 完成分析\n")


# ============================================================================
# 便捷函数（向后兼容）
# ============================================================================

# Worker 输出
def print_worker_start(name: str, task: str):
    """打印 Worker 开始工作"""
    OutputFormatter.print_worker_start(name, task)


def print_worker_thinking(name: str):
    """打印 Worker 思考过程标题"""
    OutputFormatter.print_worker_thinking(name)


def print_worker_complete(name: str):
    """打印 Worker 完成工作"""
    OutputFormatter.print_worker_complete(name)


def print_worker_warning(message: str):
    """打印 Worker 警告信息"""
    OutputFormatter.print_worker_warning(message)


def print_worker_error(message: str):
    """打印 Worker 错误信息"""
    OutputFormatter.print_worker_error(message)


# Team 输出
def print_team_start(name: str, call_id: str, task: str, workers: List[str]):
    """打印 Team Supervisor 开始协调"""
    OutputFormatter.print_team_start(name, call_id, task, workers)


def print_team_thinking(name: str):
    """打印 Team Supervisor 协调过程标题"""
    OutputFormatter.print_team_thinking(name)


def print_team_complete(name: str):
    """打印 Team Supervisor 完成协调"""
    OutputFormatter.print_team_complete(name)


def print_team_warning(message: str):
    """打印 Team Supervisor 警告信息"""
    OutputFormatter.print_team_warning(message)


def print_team_error(message: str):
    """打印 Team Supervisor 错误信息"""
    OutputFormatter.print_team_error(message)


def print_team_duplicate_warning(message: str):
    """打印 Team Supervisor 重复调用警告"""
    OutputFormatter.print_team_duplicate_warning(message)


# Global 输出
def print_global_start(task: str):
    """打印 Global Supervisor 开始分析"""
    OutputFormatter.print_global_start(task)


def print_global_thinking():
    """打印 Global Supervisor 分析过程标题"""
    OutputFormatter.print_global_thinking()


def print_global_complete():
    """打印 Global Supervisor 完成分析"""
    OutputFormatter.print_global_complete()


# 消息生成函数
def format_executed_message(name: str) -> str:
    """生成"已执行过"的返回消息"""
    return OutputFormatter.format_executed_message(name)


def format_duplicate_task_message(name: str) -> str:
    """生成"重复任务"的返回消息"""
    return OutputFormatter.format_duplicate_task_message(name)


def format_result_message(name: str, response: str) -> str:
    """生成结果消息"""
    return OutputFormatter.format_result_message(name, response)
