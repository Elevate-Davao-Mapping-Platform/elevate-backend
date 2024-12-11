import os

from aws_cdk import CfnOutput, Duration, aws_iam
from aws_cdk import aws_lambda as lambda_
from constructs import Construct


class LLMRAGAPI(Construct):
    """
    Class to create the infrastructure on AWS.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs,
    ) -> None:
        self.entity_table = kwargs.pop('entity_table', None)

        super().__init__(scope, construct_id)

        # Store the inputs
        self.construct_id = construct_id
        self.main_resources_name = os.environ['RESOURCE_NAME']
        self.stage = os.environ['DEPLOYMENT_ENVIRONMENT']

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
                aws_iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole'),
                aws_iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaVPCAccessExecutionRole'),
            ],
        )

        # Grant permission to invoke Bedrock
        lambda_role.add_to_policy(
            aws_iam.PolicyStatement(
                actions=['bedrock:InvokeModel', 'secretsmanager:GetSecretValue'],
                resources=[
                    'arn:aws:bedrock:*:*:foundation-model/anthropic.claude-v2:1',
                    'arn:aws:bedrock:*:*:foundation-model/amazon.titan-embed-text-v2:0',
                    'arn:aws:secretsmanager:*:*:secret:elevate/*',
                ],
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
        north_virginia_region = 'us-east-1'
        current_region = os.getenv('AWS_REGION')
        self.lambda_rag_api = lambda_.DockerImageFunction(
            self,
            f'{self.main_resources_name}-llm-service-{self.stage}',
            function_name=f'{self.main_resources_name}-llm-service-{self.stage}',
            code=lambda_.DockerImageCode.from_image_asset(
                'src/rag_api',
                exclude=['*.pyc', '.pytest_cache', '__pycache__'],
            ),
            timeout=Duration.seconds(60 * 5),  # 5 minutes
            memory_size=1024,
            environment={
                'STAGE': self.stage,
                'LOG_LEVEL': 'DEBUG' if self.stage == 'dev' else 'INFO',
                'POWERTOOLS_SERVICE_NAME': 'llm-service',
                'POWERTOOLS_LOGGER_LOG_EVENT': 'true',
                'BEDROCK_AWS_REGION': north_virginia_region,
                'ENTITIES_TABLE': self.entity_table.table_name,
                'REGION': current_region,
            },
            architecture=lambda_.Architecture.X86_64,
            role=lambda_role,
        )

    def generate_cloudformation_outputs(self):
        """
        Method to add the relevant CloudFormation outputs.
        """
        CfnOutput(
            self,
            'DeploymentEnvironment',
            value=self.stage,
            description='Deployment environment',
        )

        CfnOutput(
            self,
            'FunctionArn',
            value=self.lambda_rag_api.function_arn,
            description='Function ARN',
        )
