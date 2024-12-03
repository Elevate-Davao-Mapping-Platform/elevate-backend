import os
from aws_cdk import (
    aws_lambda as lambda_,
    Duration,
    CfnOutput,
    RemovalPolicy,
    aws_iam,
)
from constructs import Construct
from aws_cdk.aws_lambda_python_alpha import PythonFunction, PythonLayerVersion, BundlingOptions


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
        super().__init__(scope, construct_id)

        # Store the inputs
        self.construct_id = construct_id
        self.main_resources_name = os.environ['RESOURCE_NAME']
        self.stage = os.environ['DEPLOYMENT_ENVIRONMENT']

        # Create resources
        self.create_lambda_layers()
        self.create_lambda_functions()
        self.generate_cloudformation_outputs()

    def create_lambda_layers(self):
        """
        Create the Lambda layers that are necessary for the additional runtime
        dependencies of the Lambda Functions using PythonLayerVersion.
        """
        self.lambda_layer_llm_rag_api = PythonLayerVersion(
            self,
            f'LambdaLayer-LLM-RAG-API-{self.stage}',
            layer_version_name=f'{self.main_resources_name}-layer-{self.stage}',
            entry='lambdas/rag_api/layers',  # Directory containing requirements.txt
            compatible_runtimes=[
                lambda_.Runtime.PYTHON_3_10,
            ],
            description='Lambda Layer for Python with Bedrock and dependencies',
            compatible_architectures=[lambda_.Architecture.X86_64],
            removal_policy=RemovalPolicy.DESTROY,
        )

    def create_lambda_functions(self):
        """
        Create the Lambda Functions for the FastAPI server using PythonFunction construct
        and create a Function URL to expose it.
        """
        log_level = 'DEBUG' if self.stage == 'dev' else 'INFO'

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
                actions=['bedrock:InvokeModel'],
                resources=[
                    'arn:aws:bedrock:*:*:inference-profile/us.anthropic.claude-3-5-haiku-20241022-v1:0',
                    'arn:aws:bedrock:*:*:foundation-model/anthropic.claude-3-5-haiku-20241022-v1:0',
                ],
            )
        )

        # Create the Lambda function
        self.lambda_rag_api = PythonFunction(
            self,
            f'Lambda-LLM-RAG-API-{self.stage}',
            function_name=f'{self.main_resources_name}-app-{self.stage}',
            runtime=lambda_.Runtime.PYTHON_3_10,
            handler='handler',
            entry='lambdas/rag_api',
            index='index.py',
            timeout=Duration.seconds(120),
            memory_size=1024,
            environment={
                'STAGE': self.stage,
                'LOG_LEVEL': log_level,
            },
            layers=[
                self.lambda_layer_llm_rag_api,
            ],
            bundling=BundlingOptions(
                asset_excludes=[
                    '**/__pycache__',
                ],
            ),
            role=lambda_role,
        )

        # Add inside the ElevateBeStack class after creating the API
        self.lambda_rag_api.add_environment('POWERTOOLS_SERVICE_NAME', 'rag-api')
        self.lambda_rag_api.add_environment('POWERTOOLS_LOGGER_LOG_EVENT', 'true')

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
            'FunctionUrl',
            value=self.lambda_rag_api.function_arn,
            description='Function ARN',
        )
