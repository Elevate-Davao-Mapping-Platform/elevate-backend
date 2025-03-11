from dataclasses import dataclass
from typing import Optional

from aws_cdk import Environment
from constructs import Construct


@dataclass
class LambdaConfig:
    memory_size: int = 512
    timeout_seconds: int = 120
    runtime_version: str = '3.12'
    architecture: str = 'x86_64'


@dataclass
class BedrockConfig:
    haiku_model_id: str = 'anthropic.claude-3-5-haiku-20241022-v1:0'
    haiku_model_arn: str = 'us.anthropic.claude-3-5-haiku-20241022-v1:0'
    nova_model_id: str = 'amazon.nova-micro-v1:0'
    nova_model_arn: str = 'us.amazon.nova-micro-v1:0'
    sonnet_model_id: str = 'anthropic.claude-3-5-sonnet-20241022-v2:0'
    sonnet_model_arn: str = 'apac.anthropic.claude-3-5-sonnet-20241022-v2:0'


class Config:
    """Centralized configuration management for the CDK app"""

    def __init__(
        self,
        scope: Construct,
        stage: str,
        main_resources_name: str,
        env: Optional[Environment] = None,
    ):
        # Core settings
        self.stage = stage
        self.main_resources_name = main_resources_name
        self.env = env

        # Context values
        self.region = 'ap-southeast-1'
        self.bedrock_region = 'us-east-1'

        self.account_id = env.account if env else scope.node.try_get_context('account')

        # Environment-specific settings
        self.is_prod = stage == 'prod'
        self.log_level = 'INFO' if self.is_prod else 'DEBUG'

        # Component configurations
        self.lambda_config = LambdaConfig()
        self.bedrock_config = BedrockConfig()

    @property
    def resource_name_prefix(self) -> str:
        return f'{self.main_resources_name}-{self.stage}'

    def get_lambda_env_vars(self, additional_vars: dict = None) -> dict:
        """Get common Lambda environment variables"""
        base_vars = {
            'STAGE': self.stage,
            'LOG_LEVEL': self.log_level,
            'REGION': self.region,
            'AWS_REGION': self.region,
        }
        return {**base_vars, **(additional_vars or {})}

    def get_tags(self) -> dict:
        """Get common tags for resources"""
        return {
            'Environment': self.stage,
            'Application': self.main_resources_name,
            'ManagedBy': 'CDK',
        }

    def get_bedrock_arn(self, resource_type: str, model_id: str) -> str:
        """Get Bedrock ARN for a specific resource type"""
        return f'arn:aws:bedrock:{self.region}:{self.account_id}:' f'{resource_type}/{model_id}'
