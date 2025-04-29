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
        account_id: str,
        env: Optional[Environment] = None,
    ):
        # Core settings
        self.stage = stage
        self.main_resources_name = main_resources_name
        self.env = env
        self.prefix = f'{main_resources_name}-{stage}'
        self.prefix_no_symbols = f'{main_resources_name}{stage}'

        # Context values
        self.region = 'ap-southeast-1'
        self.bedrock_region = 'us-east-1'

        self.account_id = account_id

        # Environment-specific settings
        self.is_prod = stage == 'prod'
        self.log_level = 'INFO' if self.is_prod else 'DEBUG'

        # Component configurations
        self.lambda_config = LambdaConfig()
        self.bedrock_config = BedrockConfig()

        self.verified_domain = 'elevate-davao.live'
        self.app_email = 'no-reply@elevate-davao.live'
        self.app_name = 'Elevate Davao'
        self.domain_cert_arn = (
            'arn:aws:acm:us-east-1:058264295349:certificate/e00d8129-7250-4226-82d9-e24249e515a1'
        )

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
