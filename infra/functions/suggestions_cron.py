from aws_cdk import CfnOutput, Duration, RemovalPolicy, aws_iam, aws_lambda, aws_logs
from aws_cdk.aws_lambda_python_alpha import (
    BundlingOptions,
    PythonFunction,
    PythonLayerVersion,
)
from constructs import Construct

from infra.config import Config


class SuggestionsCron(Construct):
    """
    Class to create the infrastructure on AWS.
    """

    def __init__(self, scope: Construct, id: str, config: Config, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.config = config

        self.create_lambda_function()
        self.generate_cloudformation_outputs()

    def create_lambda_function(self):
        """
        Create the Lambda Function for the Suggestions Cron Job
        and create necessary IAM roles and permissions.
        """
        # Define the IAM role
        lambda_role = aws_iam.Role(
            self,
            'LambdaExecutionRole',
            assumed_by=aws_iam.ServicePrincipal('lambda.amazonaws.com'),
            managed_policies=[
                aws_iam.ManagedPolicy.from_aws_managed_policy_name(
                    'service-role/AWSLambdaBasicExecutionRole'
                ),
                aws_iam.ManagedPolicy.from_aws_managed_policy_name(
                    'service-role/AWSLambdaVPCAccessExecutionRole'
                ),
            ],
        )

        # Grant permission to invoke Bedrock
        lambda_role.add_to_policy(
            aws_iam.PolicyStatement(
                actions=['bedrock:InvokeModel', 'bedrock:InvokeModelWithResponseStream'],
                resources=[
                    'arn:aws:bedrock:*:*:inference-profile/us.anthropic.claude-3-5-haiku-20241022-v1:0',
                    'arn:aws:bedrock:*:*:foundation-model/anthropic.claude-3-5-haiku-20241022-v1:0',
                ],
            )
        )

        lambda_role.add_to_policy(
            aws_iam.PolicyStatement(
                actions=['bedrock:Retrieve'],
                resources=['arn:aws:bedrock:us-east-1:058264295349:knowledge-base/ORGCXIYNDH'],
            )
        )

        # Create the Lambda function using Docker
        self.suggestions_cron_layer = PythonLayerVersion(
            self,
            f'{self.config.prefix}-suggestions-cron-layer',
            layer_version_name=f'{self.config.prefix}-suggestions-cron-layer',
            entry='src/suggestions_cron/layer',
            compatible_runtimes=[aws_lambda.Runtime.PYTHON_3_12],
            compatible_architectures=[aws_lambda.Architecture.X86_64],
            description='Dependencies for Suggestions Cron Job Lambda',
            removal_policy=RemovalPolicy.DESTROY,
            bundling=BundlingOptions(
                asset_excludes=[
                    '**/__pycache__',
                ],
            ),
        )

        self.lambda_suggestions_cron = PythonFunction(
            self,
            f'{self.config.prefix}-suggestions-cron',
            function_name=f'{self.config.prefix}-suggestions-cron',
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            handler='handler',
            entry='src',
            index='suggestions_cron/handler.py',
            timeout=Duration.minutes(2),
            log_retention=aws_logs.RetentionDays.ONE_MONTH,
            memory_size=512,
            environment={
                'STAGE': self.config.stage,
                'LOG_LEVEL': self.config.log_level,
                'REGION': self.config.region,
                'BEDROCK_AWS_REGION': self.config.bedrock_region,
                'POWERTOOLS_LOG_LEVEL': 'DEBUG' if self.config.stage == 'dev' else 'INFO',
                'POWERTOOLS_SERVICE_NAME': f'{self.config.prefix}-suggestions-service',
                'POWERTOOLS_LOGGER_LOG_EVENT': 'true' if self.config.stage == 'dev' else 'false',
            },
            role=lambda_role,
            layers=[self.suggestions_cron_layer],
            bundling=BundlingOptions(
                asset_excludes=['**/__pycache__', 'local_tests', 'generate_suggestions'],
            ),
        )

    def generate_cloudformation_outputs(self):
        """
        Method to add the relevant CloudFormation outputs.
        """
        CfnOutput(
            self,
            'FunctionArn',
            value=self.lambda_suggestions_cron.function_arn,
            description='Function ARN',
        )
