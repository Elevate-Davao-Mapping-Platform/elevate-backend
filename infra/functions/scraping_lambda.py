from aws_cdk import CfnOutput, Duration, RemovalPolicy, aws_iam, aws_lambda, aws_logs
from aws_cdk.aws_lambda_python_alpha import (
    BundlingOptions,
    PythonFunction,
    PythonLayerVersion,
)
from constructs import Construct

from infra.config import Config
from infra.functions.lambda_utils import LambdaUtils


class ScrapingLambda(Construct):
    """
    Class to create the infrastructure on AWS.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: Config,
        **kwargs,
    ) -> None:
        self.common_dependencies_layer: PythonLayerVersion = kwargs.pop(
            'common_dependencies_layer', None
        )

        super().__init__(scope, construct_id)

        # Store the inputs
        self.config = config

        # Create resources
        self.create_lambda_function()
        self.generate_cloudformation_outputs()

    def create_lambda_function(self):
        """
        Create the Lambda Function the Scraping Lambda and create necessary IAM roles and permissions.
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

        # Add S3 permissions
        lambda_role.add_to_policy(
            aws_iam.PolicyStatement(
                actions=['s3:PutObject', 's3:GetObject', 's3:ListBucket'],
                resources=[
                    'arn:aws:s3:::elevate-rag-documents-*/*',
                    'arn:aws:s3:::elevate-rag-documents-*',
                ],
            )
        )

        # Create the Lambda function using Docker
        self.scraping_lambda_layer = PythonLayerVersion(
            self,
            f'{self.config.prefix}-scraping-lambda-layer',
            layer_version_name=f'{self.config.prefix}-scraping-lambda-layer',
            entry='src/scraping/layer',
            compatible_runtimes=[aws_lambda.Runtime.PYTHON_3_12],
            compatible_architectures=[aws_lambda.Architecture.X86_64],
            description='Dependencies for Scraping Lambda',
            removal_policy=RemovalPolicy.DESTROY,
            bundling=BundlingOptions(
                asset_excludes=[
                    '**/__pycache__',
                ],
            ),
        )

        self.scraping_lambda = PythonFunction(
            self,
            f'{self.config.prefix}-scraping-lambda',
            function_name=f'{self.config.prefix}-scraping-lambda',
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            handler='handler',
            entry='src',
            index='scraping/handler.py',
            timeout=Duration.minutes(2),
            log_retention=aws_logs.RetentionDays.ONE_MONTH,
            memory_size=512,
            environment={
                'STAGE': self.config.stage,
                'LOG_LEVEL': self.config.log_level,
                'REGION': self.config.region,
                'POWERTOOLS_LOG_LEVEL': 'DEBUG' if self.config.stage == 'dev' else 'INFO',
                'POWERTOOLS_SERVICE_NAME': f'{self.config.prefix}-scraping-service',
                'POWERTOOLS_LOGGER_LOG_EVENT': 'true' if self.config.stage == 'dev' else 'false',
            },
            role=lambda_role,
            layers=[self.scraping_lambda_layer, self.common_dependencies_layer],
            bundling=BundlingOptions(
                asset_excludes=LambdaUtils.get_asset_excludes(['scraping', 'shared_modules']),
            ),
        )

    def generate_cloudformation_outputs(self):
        """
        Method to add the relevant CloudFormation outputs.
        """
        CfnOutput(
            self,
            'DeploymentEnvironment',
            value=self.config.stage,
            description='Deployment environment',
        )

        CfnOutput(
            self,
            'FunctionArn',
            value=self.scraping_lambda.function_arn,
            description='Function ARN',
        )
