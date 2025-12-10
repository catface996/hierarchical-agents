"""
配置管理模块 - 统一管理系统配置和敏感信息

支持多种配置方式:
1. 环境变量
2. .env 文件
3. 配置文件 (config.json)
"""

import os
from typing import Optional
from pathlib import Path


class Config:
    """配置管理类 - 单例模式"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._aws_bedrock_api_key: Optional[str] = None
            self._model_id: str = "us.anthropic.claude-sonnet-4-20250514-v1:0"
            self._initialized = True
    
    def load_from_env(self) -> 'Config':
        """从环境变量加载配置"""
        self._aws_bedrock_api_key = os.environ.get('AWS_BEDROCK_API_KEY')
        model_id = os.environ.get('AWS_BEDROCK_MODEL_ID')
        if model_id:
            self._model_id = model_id
        return self
    
    def load_from_dotenv(self, dotenv_path: str = '.env') -> 'Config':
        """从 .env 文件加载配置"""
        env_file = Path(dotenv_path)
        if not env_file.exists():
            return self
        
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    
                    if key == 'AWS_BEDROCK_API_KEY':
                        self._aws_bedrock_api_key = value
                    elif key == 'AWS_BEDROCK_MODEL_ID':
                        self._model_id = value
        
        return self
    
    def set_api_key(self, api_key: str) -> 'Config':
        """手动设置 API Key"""
        self._aws_bedrock_api_key = api_key
        return self
    
    def set_model_id(self, model_id: str) -> 'Config':
        """手动设置模型 ID"""
        self._model_id = model_id
        return self
    
    @property
    def aws_bedrock_api_key(self) -> Optional[str]:
        """获取 AWS Bedrock API Key"""
        return self._aws_bedrock_api_key
    
    @property
    def model_id(self) -> str:
        """获取模型 ID"""
        return self._model_id
    
    def setup_environment(self) -> None:
        """将配置设置到环境变量中（供 Strands SDK 使用）"""
        if self._aws_bedrock_api_key:
            os.environ['AWS_BEDROCK_API_KEY'] = self._aws_bedrock_api_key
        if self._model_id:
            os.environ['AWS_BEDROCK_MODEL_ID'] = self._model_id
    
    def is_configured(self) -> bool:
        """检查是否已配置 API Key"""
        return self._aws_bedrock_api_key is not None
    
    def validate(self) -> None:
        """验证配置是否完整"""
        if not self._aws_bedrock_api_key:
            raise ValueError(
                "AWS Bedrock API Key 未配置。请通过以下方式之一配置:\n"
                "1. 环境变量: export AWS_BEDROCK_API_KEY='your-key'\n"
                "2. .env 文件: 创建 .env 文件并添加 AWS_BEDROCK_API_KEY=your-key\n"
                "3. 代码设置: config.set_api_key('your-key')"
            )


# ============================================================================
# 便捷函数
# ============================================================================

def get_config() -> Config:
    """获取配置实例（单例）"""
    return Config()


def setup_config(
    api_key: Optional[str] = None,
    model_id: Optional[str] = None,
    use_dotenv: bool = True,
    use_env: bool = True
) -> Config:
    """
    设置配置并返回配置实例
    
    Args:
        api_key: 直接提供的 API Key（优先级最高）
        model_id: 模型 ID
        use_dotenv: 是否从 .env 文件加载
        use_env: 是否从环境变量加载
    
    Returns:
        Config 实例
    
    优先级顺序:
    1. 直接提供的参数（api_key, model_id）
    2. 环境变量
    3. .env 文件
    """
    config = get_config()
    
    # 从 .env 文件加载（优先级最低）
    if use_dotenv:
        config.load_from_dotenv()
    
    # 从环境变量加载（优先级中等）
    if use_env:
        config.load_from_env()
    
    # 直接设置（优先级最高）
    if api_key:
        config.set_api_key(api_key)
    if model_id:
        config.set_model_id(model_id)
    
    # 设置到环境变量
    config.setup_environment()
    
    return config


def ensure_configured() -> Config:
    """
    确保配置已设置，如果未设置则尝试自动加载
    
    Returns:
        Config 实例
    
    Raises:
        ValueError: 如果配置未设置且无法自动加载
    """
    config = get_config()
    
    if not config.is_configured():
        # 尝试自动加载
        config.load_from_dotenv().load_from_env()
        config.setup_environment()
    
    # 验证配置
    config.validate()
    
    return config


# ============================================================================
# 示例用法
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("配置管理模块示例")
    print("=" * 80)
    
    # 方式 1: 自动加载（从环境变量或 .env 文件）
    print("\n【方式 1: 自动加载】")
    config = setup_config()
    print(f"API Key 已配置: {config.is_configured()}")
    print(f"模型 ID: {config.model_id}")
    
    # 方式 2: 手动设置
    print("\n【方式 2: 手动设置】")
    config = setup_config(
        api_key="your-api-key-here",
        model_id="us.anthropic.claude-sonnet-4-20250514-v1:0"
    )
    print(f"API Key 已配置: {config.is_configured()}")
    print(f"模型 ID: {config.model_id}")
    
    # 方式 3: 确保已配置（推荐在应用启动时使用）
    print("\n【方式 3: 确保已配置】")
    try:
        config = ensure_configured()
        print("✓ 配置验证通过")
    except ValueError as e:
        print(f"✗ 配置验证失败: {e}")
    
    print("\n" + "=" * 80)
