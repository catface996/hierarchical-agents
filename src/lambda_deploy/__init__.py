"""
Lambda - AWS Lambda 部署模块

用于 AWS Lambda + API Gateway 部署场景
"""

from .handler import lambda_handler, health_check_handler

__all__ = ['lambda_handler', 'health_check_handler']
