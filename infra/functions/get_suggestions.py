from aws_cdk import CfnOutput, Duration, aws_iam, aws_lambda, aws_logs
from aws_cdk.aws_lambda_python_alpha import (
    BundlingOptions,
    PythonFunction,
    PythonLayerVersion,
)
from constructs import Construct

from infra.config import Config
from infra.dynamodb.entity_table import EntityTable


class GetSuggestions(Construct):
    """
    Class to create the infrastructure on AWS.
    """

    def __init__(self, scope: Construct, id: str, config: Config, **kwargs) -> None:
        self.common_dependencies_layer: PythonLayerVersion = kwargs.pop(
            'common_dependencies_layer', None
        )
        self.entity_table: EntityTable = kwargs.pop('entity_table', None)

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

        lambda_role.add_to_policy(
            aws_iam.PolicyStatement(
                actions=[
                    'dynamodb:Query',
                    'dynamodb:BatchGetItem',
                ],
                resources=[self.entity_table.table_arn],
            )
        )

        self.get_suggestions_lambda = PythonFunction(
            self,
            f'{self.config.prefix}-get-suggestions',
            function_name=f'{self.config.prefix}-get-suggestions',
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            handler='handler',
            entry='src',
            index='get_suggestions/handler.py',
            timeout=Duration.minutes(2),
            log_retention=aws_logs.RetentionDays.ONE_MONTH,
            memory_size=512,
            environment={
                'STAGE': self.config.stage,
                'LOG_LEVEL': self.config.log_level,
                'REGION': self.config.region,
                'ENTITIES_TABLE': self.entity_table.table_name,
                'POWERTOOLS_LOG_LEVEL': 'DEBUG' if self.config.stage == 'dev' else 'INFO',
                'POWERTOOLS_SERVICE_NAME': f'{self.config.prefix}-get-suggestions-service',
                'POWERTOOLS_LOGGER_LOG_EVENT': 'true' if self.config.stage == 'dev' else 'false',
            },
            role=lambda_role,
            layers=[self.common_dependencies_layer],
            bundling=BundlingOptions(
                asset_excludes=['**/__pycache__', 'local_tests', 'generate_suggestions', 'rag_api'],
            ),
        )

    def generate_cloudformation_outputs(self):
        """
        Method to add the relevant CloudFormation outputs.
        """
        CfnOutput(
            self,
            'FunctionArn',
            value=self.get_suggestions_lambda.function_arn,
            description='Function ARN',
        )
