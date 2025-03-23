from aws_cdk import CfnOutput, Duration, RemovalPolicy, aws_iam, aws_lambda, aws_logs
from aws_cdk.aws_lambda_python_alpha import (
    BundlingOptions,
    PythonFunction,
    PythonLayerVersion,
)
from constructs import Construct

from infra.appsync.appsync import AppsyncAPI
from infra.config import Config


class LLMRAGAPI(Construct):
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
        self.entity_table = kwargs.pop('entity_table', None)
        self.appsync_api = kwargs.pop('appsync_api', None)

        super().__init__(scope, construct_id)

        # Store the inputs
        self.config = config

        # Create resources
        self.create_lambda_function()
        self.generate_cloudformation_outputs()

    def create_lambda_function(self):
        """
        Create the Lambda Function using Docker image for the FastAPI server
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

        # Add the entity table to the Lambda function environment variables
        lambda_role.add_to_policy(
            aws_iam.PolicyStatement(
                actions=[
                    'dynamodb:Query',
                    'dynamodb:GetItem',
                    'dynamodb:PutItem',
                    'dynamodb:Scan',
                ],
                resources=[self.entity_table.table_arn],
            )
        )

        # Create the Lambda function using Docker
        self.rag_api_layer = PythonLayerVersion(
            self,
            f'{self.config.prefix}-rag-api-layer',
            layer_version_name=f'{self.config.prefix}-rag-api-layer',
            entry='src/rag_api/layer',
            compatible_runtimes=[aws_lambda.Runtime.PYTHON_3_12],
            compatible_architectures=[aws_lambda.Architecture.X86_64],
            description='Dependencies for RAG API Lambda',
            removal_policy=RemovalPolicy.DESTROY,
            bundling=BundlingOptions(
                asset_excludes=[
                    '**/__pycache__',
                ],
            ),
        )

        self.lambda_rag_api = PythonFunction(
            self,
            f'{self.config.prefix}-rag-api',
            function_name=f'{self.config.prefix}-rag-api',
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            handler='handler',
            entry='src',
            index='rag_api/handler.py',
            timeout=Duration.seconds(120),
            log_retention=aws_logs.RetentionDays.ONE_MONTH,
            memory_size=512,
            environment={
                'STAGE': self.config.stage,
                'LOG_LEVEL': self.config.log_level,
                'REGION': self.config.region,
                'BEDROCK_AWS_REGION': self.config.bedrock_region,
                'ENTITIES_TABLE': self.entity_table.table_name,
                'KNOWLEDGE_BASE_ID': 'ORGCXIYNDH',
                'POWERTOOLS_LOG_LEVEL': 'DEBUG',
                'POWERTOOLS_SERVICE_NAME': 'elevate-dev-llm-service',
                'POWERTOOLS_LOGGER_LOG_EVENT': 'true',
            },
            role=lambda_role,
            layers=[self.rag_api_layer],
            bundling=BundlingOptions(
                asset_excludes=[
                    '**/__pycache__',
                    'local_tests',
                ],
            ),
        )

    def set_appsync_api(self, appsync_api: AppsyncAPI):
        """
        Set the AppSync API for the Lambda function.

        :param AppsyncAPI appsync_api: The AppSync API to set.
        """
        self.appsync_api = appsync_api
        self.lambda_rag_api.add_environment('GRAPHQL_URL', self.appsync_api.graphql_url)
        self.lambda_rag_api.add_environment('API_KEY', self.appsync_api.api_key)

        self.lambda_rag_api.add_to_role_policy(
            aws_iam.PolicyStatement(
                actions=['appsync:GraphQL'],
                resources=[f'{self.appsync_api.arn}/*'],
            )
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
            value=self.lambda_rag_api.function_arn,
            description='Function ARN',
        )
